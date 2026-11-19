"""
OM3-26 Protección de la información personal.
Recorre los endpoints con cada rol para comprobar que cada quien solo ve lo suyo.
Ejecutar: python manage.py test apps.administration.test_privacy
"""
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from apps.appointments.models import Appointment
from apps.emergency.models import EmergencyChat
from apps.evaluations.models import Evaluation

from .tests import PASSWORD, AdminTestCase, User


class ProteccionDeDatosTests(AdminTestCase):
    def setUp(self):
        super().setUp()
        self.other = User.objects.create_user(email="otra@x.com", password=PASSWORD, first_name="Otra", last_name="Persona",
                                              email_verified=True)
        self.evaluation = Evaluation.objects.create(user=self.patient, total_score=10, max_score=36, percentage=28, level="LEVE")
        self.chat = EmergencyChat.objects.create(patient=self.patient)
        start = timezone.now() + timedelta(days=1)
        self.appointment = Appointment.objects.create(patient=self.patient, psychologist=self.psy, start=start,
                                                      end=start + timedelta(hours=1))

    def test_ca1_cada_usuario_accede_solo_a_su_informacion(self):
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(reverse("evaluations:evaluation-detail", args=[self.evaluation.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("evaluations:evaluation-list")).data, [])
        self.assertEqual(self.client.get(reverse("appointments:appointment-detail", args=[self.appointment.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("appointments:call", args=[self.appointment.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("emergency:chat-detail", args=[self.chat.pk])).status_code, 404)
        me = self.client.get(reverse("accounts:me")).data
        self.assertEqual(me["email"], "otra@x.com")

    def test_ca1_el_psicologo_no_ve_evaluaciones_de_pacientes(self):
        self.client.force_authenticate(self.psy)
        self.assertEqual(self.client.get(reverse("evaluations:evaluation-list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("evaluations:evaluation-detail", args=[self.evaluation.pk])).status_code, 403)

    def test_ca2_nada_personal_es_publico_sin_iniciar_sesion(self):
        self.client.force_authenticate(None)
        protected = [
            reverse("accounts:me"), reverse("accounts:users"), reverse("evaluations:evaluation-list"),
            reverse("appointments:appointment-list"), reverse("emergency:chat-list"),
            reverse("professionals:directory"), reverse("administration:users"), reverse("administration:stats"),
            reverse("appointments:slots", args=[self.psy.pk]),
        ]
        for url in protected:
            self.assertEqual(self.client.get(url).status_code, 401, url)

    def test_ca2_el_directorio_no_expone_datos_de_contacto(self):
        self.profile.is_verified = True
        self.profile.save()
        self.psy.phone = "3001234567"
        self.psy.save()
        self.client.force_authenticate(self.patient)
        item = self.client.get(reverse("professionals:directory")).data[0]
        self.assertNotIn("email", item)
        self.assertNotIn("phone", item)
        self.assertNotIn("license_number", item)

    def test_ca3_ca4_cada_rol_solo_usa_sus_funciones(self):
        self.profile.is_verified = True  # el chat de emergencia es para psicólogos verificados
        self.profile.save()
        matrix = {
            # (método, url): roles que SÍ pueden
            ("get", reverse("evaluations:evaluation-list")): {"PACIENTE"},
            ("get", reverse("emergency:chat-list")): {"PACIENTE", "PSICOLOGO"},
            ("get", reverse("appointments:my-availability")): {"PSICOLOGO"},
            ("get", reverse("professionals:me")): {"PSICOLOGO"},
            ("get", reverse("professionals:list")): {"ADMINISTRADOR"},
            ("get", reverse("accounts:users")): {"ADMINISTRADOR"},
            ("get", reverse("administration:users")): {"ADMINISTRADOR"},
            ("get", reverse("administration:logs")): {"ADMINISTRADOR"},
            ("get", reverse("administration:stats")): {"ADMINISTRADOR"},
            ("post", reverse("appointments:appointment-list")): {"PACIENTE"},
        }
        for user in (self.patient, self.psy, self.admin):
            self.client.force_authenticate(user)
            for (method, url), allowed in matrix.items():
                code = getattr(self.client, method)(url, {}, format="json").status_code
                if user.role in allowed:
                    self.assertNotEqual(code, 403, f"{user.role} debería poder usar {url}")
                else:
                    self.assertEqual(code, 403, f"{user.role} NO debería poder usar {url}")

    def test_ca4_una_cuenta_desactivada_pierde_el_acceso(self):
        login = self.client.post(reverse("accounts:login"), {"email": "ana@x.com", "password": PASSWORD}, format="json")
        token = login.data["access"]
        self.patient.is_active = False
        self.patient.save()
        self.client.force_authenticate(None)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(self.client.get(reverse("accounts:me")).status_code, 401)

    def test_el_registro_exige_aceptar_la_politica_de_datos(self):
        self.client.force_authenticate(None)
        data = {"email": "nuevo@x.com", "first_name": "N", "last_name": "P", "password": PASSWORD, "password_confirm": PASSWORD}
        response = self.client.post(reverse("accounts:register"), data, format="json")
        self.assertIn("accept_privacy", response.data)
        response = self.client.post(reverse("accounts:register"), {**data, "accept_privacy": False}, format="json")
        self.assertIn("política", str(response.data["accept_privacy"]))
        self.client.post(reverse("accounts:register"), {**data, "accept_privacy": True}, format="json")
        self.assertIsNotNone(User.objects.get(email="nuevo@x.com").privacy_accepted_at)

    def test_encabezados_de_proteccion(self):
        response = self.client.get(reverse("accounts:me"))
        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
