"""
OM3-12 Realizar evaluación emocional · OM3-13 Consultar historial emocional.
Ejecutar: python manage.py test apps.evaluations
"""
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Evaluation, Level, Question
from .scoring import interpretation, level_for, score_answers

User = get_user_model()
PASSWORD = "ClaveSegura#2026"


def make_user(email, role=User.Role.PACIENTE):
    return User.objects.create_user(email=email, password=PASSWORD, first_name="Laura", last_name="Ríos", role=role)


class EvaluationApiTestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.patient = make_user("paciente@openmind.com")
        self.client.force_authenticate(self.patient)
        self.questions = list(Question.objects.filter(is_active=True))

    def answers(self, value=1, **overrides):
        """Respuestas para todas las preguntas; overrides = {order: valor}."""
        return [{"question": q.id, "value": overrides.get(f"q{q.order}", value)} for q in self.questions]

    def submit(self, answers):
        return self.client.post(reverse("evaluations:evaluation-list"), {"answers": answers}, format="json")


class RealizarEvaluacionTests(EvaluationApiTestCase):
    def test_ca1_ca2_iniciar_muestra_preguntas_y_escala(self):
        response = self.client.get(reverse("evaluations:evaluation-questions"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["questions"]), 12)
        self.assertEqual([o["value"] for o in response.data["scale"]], [0, 1, 2, 3])
        self.assertEqual(response.data["questions"][0]["order"], 1)
        self.assertIn("instructions", response.data)

    def test_preguntas_inactivas_no_se_muestran(self):
        Question.objects.filter(order=12).update(is_active=False)
        response = self.client.get(reverse("evaluations:evaluation-questions"))
        self.assertEqual(len(response.data["questions"]), 11)

    def test_ca3_debe_responder_todas_las_preguntas(self):
        response = self.submit(self.answers()[:-2])

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Faltan respuestas para las preguntas: 11, 12", str(response.data["answers"]))
        self.assertFalse(Evaluation.objects.exists())

    def test_ca3_sin_respuestas(self):
        response = self.submit([])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(reverse("evaluations:evaluation-list"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_respuesta_fuera_de_rango(self):
        response = self.submit(self.answers(value=5))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pregunta_repetida_o_inexistente(self):
        answers = self.answers()
        response = self.submit(answers + [answers[0]])
        self.assertIn("una sola vez", str(response.data))
        response = self.submit(answers + [{"question": 9999, "value": 1}])
        self.assertIn("no válidas", str(response.data))

    def test_ca4_ca5_procesa_y_muestra_resultado(self):
        response = self.submit(self.answers(value=0))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["total_score"], 0)
        self.assertEqual(response.data["max_score"], 36)
        self.assertEqual(response.data["level"], Level.ESTABLE)
        self.assertEqual(len(response.data["dimension_scores"]), 4)
        self.assertEqual(len(response.data["answers"]), 12)
        self.assertIn("summary", response.data["interpretation"])
        self.assertIn("no reemplaza", response.data["interpretation"]["disclaimer"])
        self.assertFalse(response.data["needs_support"])

    def test_malestar_alto_recomienda_apoyo(self):
        response = self.submit(self.answers(value=3))
        self.assertEqual(response.data["level"], Level.ALTO)
        self.assertTrue(response.data["needs_support"])
        self.assertTrue(any("chat de emergencia" in r for r in response.data["interpretation"]["recommendations"]))

    def test_pregunta_de_alerta_activa_apoyo_aunque_el_total_sea_bajo(self):
        critical = Question.objects.get(is_critical=True)
        response = self.submit(self.answers(value=0, **{f"q{critical.order}": 3}))
        self.assertEqual(response.data["level"], Level.ESTABLE)
        self.assertTrue(response.data["needs_support"])

    def test_solo_pacientes_pueden_evaluarse(self):
        self.client.force_authenticate(make_user("psico@openmind.com", User.Role.PSICOLOGO))
        self.assertEqual(self.client.get(reverse("evaluations:evaluation-questions")).status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(reverse("evaluations:evaluation-questions")).status_code, 401)


class HistorialEmocionalTests(EvaluationApiTestCase):
    def test_ca1_ca2_ca3_muestra_evaluaciones_anteriores_con_fecha(self):
        self.submit(self.answers(value=2))
        self.submit(self.answers(value=0))

        response = self.client.get(reverse("evaluations:evaluation-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertIn("created_at", response.data[0])
        # la más reciente primero
        self.assertEqual(response.data[0]["level"], Level.ESTABLE)
        self.assertEqual(response.data[1]["level"], Level.MODERADO)

    def test_ca4_consultar_resultado_de_cada_evaluacion(self):
        evaluation_id = self.submit(self.answers(value=1)).data["id"]
        response = self.client.get(reverse("evaluations:evaluation-detail", args=[evaluation_id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["level"], Level.LEVE)
        self.assertEqual(response.data["answers"][0]["value_label"], "Algunos días")

    def test_historial_vacio(self):
        response = self.client.get(reverse("evaluations:evaluation-list"))
        self.assertEqual(response.data, [])

    def test_ca5_historial_solo_del_usuario_correspondiente(self):
        evaluation_id = self.submit(self.answers()).data["id"]
        self.client.force_authenticate(make_user("otro@openmind.com"))

        self.assertEqual(self.client.get(reverse("evaluations:evaluation-list")).data, [])
        response = self.client.get(reverse("evaluations:evaluation-detail", args=[evaluation_id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_ca5_admin_y_psicologo_no_ven_historiales(self):
        self.submit(self.answers())
        admin = User.objects.create_superuser(email="admin@openmind.com", password=PASSWORD, first_name="A", last_name="B")
        self.client.force_authenticate(admin)
        self.assertEqual(self.client.get(reverse("evaluations:evaluation-list")).status_code, 403)


class ScoringTests(APITestCase):
    def test_niveles_por_porcentaje(self):
        self.assertEqual(level_for(0), Level.ESTABLE)
        self.assertEqual(level_for(25), Level.ESTABLE)
        self.assertEqual(level_for(26), Level.LEVE)
        self.assertEqual(level_for(51), Level.MODERADO)
        self.assertEqual(level_for(100), Level.ALTO)
        self.assertEqual(level_for(150), Level.ALTO)

    def test_puntaje_por_dimension_e_interpretacion(self):
        questions = list(Question.objects.all())
        pairs = [(q, 3 if q.dimension == "ANSIEDAD" else 0) for q in questions]
        result = score_answers(pairs)

        self.assertEqual(result["dimension_scores"]["ANSIEDAD"]["percentage"], 100)
        self.assertEqual(result["dimension_scores"]["ANIMO"]["percentage"], 0)
        evaluation = Evaluation(**result)
        self.assertEqual(interpretation(evaluation)["focus_dimension"], "Ansiedad")

    def test_representacion(self):
        question = Question.objects.get(order=1)
        self.assertTrue(str(question).startswith("1. "))
        user = make_user("x@x.com")
        evaluation = Evaluation.objects.create(user=user, **score_answers([(question, 0)]))
        self.assertIn("Bienestar estable", str(evaluation))

    def test_sin_respuestas(self):
        result = score_answers([])
        self.assertEqual(result["percentage"], 0)
        self.assertIsNone(interpretation(Evaluation(**result))["focus_dimension"])
