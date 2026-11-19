"""
Sprint 4: OM3-24 Gestionar usuarios · OM3-25 Estadísticas.
Ejecutar: python manage.py test apps.administration
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.appointments.models import Appointment
from apps.emergency.models import EmergencyChat
from apps.evaluations.models import Evaluation
from apps.professionals.models import PsychologistProfile

from .models import AdminActionLog

User = get_user_model()
PASSWORD = "ClaveSegura#2026"


class AdminTestCase(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="admin@x.com", password=PASSWORD, first_name="Ada", last_name="Admin")
        self.patient = User.objects.create_user(email="ana@x.com", password=PASSWORD, first_name="Ana", last_name="Ríos",
                                                email_verified=True)
        self.psy = User.objects.create_user(email="psi@x.com", password=PASSWORD, first_name="Pablo", last_name="Gil",
                                            role=User.Role.PSICOLOGO, email_verified=True)
        self.profile = PsychologistProfile.objects.create(
            user=self.psy, specialty="CLINICA", years_experience=3, license_number="TP-2222",
            description="Psicólogo clínico para adultos con ansiedad y estrés laboral.",
        )
        self.client.force_authenticate(self.admin)


# --------------------------------------------------------------------- OM3-24
class GestionarUsuariosTests(AdminTestCase):
    def test_ca1_ca2_consulta_usuarios_con_informacion_basica(self):
        response = self.client.get(reverse("administration:users"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)
        item = next(u for u in response.data if u["email"] == "psi@x.com")
        for field in ("full_name", "role_display", "is_active", "email_verified", "date_joined", "last_login"):
            self.assertIn(field, item)
        self.assertIs(item["is_verified"], False)
        self.assertNotIn("password", item)
        detail = self.client.get(reverse("administration:user-detail", args=[self.patient.pk])).data
        self.assertIsNone(detail["is_verified"])

    def test_ca1_filtros_y_busqueda(self):
        url = reverse("administration:users")
        self.assertEqual([u["email"] for u in self.client.get(url, {"role": "psicologo"}).data], ["psi@x.com"])
        self.assertEqual([u["email"] for u in self.client.get(url, {"q": "ana ríos"}).data], ["ana@x.com"])
        self.patient.is_active = False
        self.patient.save()
        self.assertEqual([u["email"] for u in self.client.get(url, {"status": "inactive"}).data], ["ana@x.com"])

    def test_ca3_ca4_desactivar_y_activar_queda_registrado(self):
        url = reverse("administration:user-status", args=[self.patient.pk])
        response = self.client.post(url, {"is_active": False, "reason": "Uso indebido del chat"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["is_active"])
        # la cuenta desactivada ya no puede iniciar sesión
        self.client.force_authenticate(None)
        login = self.client.post(reverse("accounts:login"), {"email": "ana@x.com", "password": PASSWORD}, format="json")
        self.assertEqual(login.status_code, 401)

        self.client.force_authenticate(self.admin)
        self.client.post(url, {"is_active": True}, format="json")
        logs = self.client.get(reverse("administration:logs"), {"user": self.patient.pk}).data
        self.assertEqual([log["action"] for log in logs], ["USER_ACTIVATED", "USER_DEACTIVATED"])
        self.assertEqual(logs[1]["actor_email"], "admin@x.com")
        self.assertEqual(logs[1]["reason"], "Uso indebido del chat")
        self.assertIn("Desactivó", str(AdminActionLog.objects.last()))

    def test_ca3_respeta_los_permisos_establecidos(self):
        own = self.client.post(reverse("administration:user-status", args=[self.admin.pk]), {"is_active": False, "reason": "x"}, format="json")
        self.assertIn("propia cuenta", own.data["detail"])
        other_admin = User.objects.create_superuser(email="otro@x.com", password=PASSWORD, first_name="O", last_name="A")
        response = self.client.post(reverse("administration:user-status", args=[other_admin.pk]), {"is_active": False, "reason": "x"}, format="json")
        self.assertIn("administrador", response.data["detail"])
        no_reason = self.client.post(reverse("administration:user-status", args=[self.psy.pk]), {"is_active": False}, format="json")
        self.assertIn("reason", no_reason.data)
        self.assertEqual(self.client.post(reverse("administration:user-status", args=[self.psy.pk]), {}, format="json").status_code, 400)
        self.assertFalse(AdminActionLog.objects.exists())

    def test_ca4_verificar_psicologos_tambien_queda_registrado(self):
        self.client.post(reverse("professionals:verify", args=[self.profile.pk]), {"is_verified": True}, format="json")
        self.client.post(reverse("professionals:verify", args=[self.profile.pk]), {"is_verified": True}, format="json")  # sin cambio
        self.client.post(reverse("professionals:verify", args=[self.profile.pk]), {"is_verified": False}, format="json")
        actions = list(AdminActionLog.objects.values_list("action", flat=True))
        self.assertEqual(actions, ["PROFESSIONAL_UNVERIFIED", "PROFESSIONAL_VERIFIED"])

    def test_solo_el_administrador_gestiona_usuarios(self):
        for user in (self.patient, self.psy):
            self.client.force_authenticate(user)
            for name, args in (("users", []), ("user-detail", [self.patient.pk]), ("logs", [])):
                self.assertEqual(self.client.get(reverse(f"administration:{name}", args=args)).status_code, 403)
            status_url = reverse("administration:user-status", args=[self.patient.pk])
            self.assertEqual(self.client.post(status_url, {"is_active": False}).status_code, 403)


# --------------------------------------------------------------------- OM3-25
class EstadisticasTests(AdminTestCase):
    url = reverse("administration:stats")

    def test_ca1_ca2_el_administrador_accede_y_ve_estadisticas(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        for block in ("users", "psychologists", "evaluations", "appointments", "emergency", "monthly"):
            self.assertIn(block, response.data)
        self.assertEqual(len(response.data["monthly"]["registrations"]), 6)

    def test_ca3_los_datos_corresponden_a_lo_registrado(self):
        Evaluation.objects.create(user=self.patient, total_score=30, max_score=36, percentage=83, level="ALTO", needs_support=True)
        Evaluation.objects.create(user=self.patient, total_score=6, max_score=36, percentage=17, level="ESTABLE")
        start = timezone.now() + timedelta(days=1)
        Appointment.objects.create(patient=self.patient, psychologist=self.psy, start=start, end=start + timedelta(hours=1))
        EmergencyChat.objects.create(patient=self.patient)
        self.patient.is_active = False
        self.patient.save()

        data = self.client.get(self.url).data
        by_role = {r["key"]: r["count"] for r in data["users"]["by_role"]}
        self.assertEqual(by_role, {"PACIENTE": 1, "PSICOLOGO": 1, "ADMINISTRADOR": 1})
        self.assertEqual((data["users"]["total"], data["users"]["active"], data["users"]["inactive"]), (3, 2, 1))
        self.assertEqual(data["psychologists"], {"verified": 0, "pending": 1})
        self.assertEqual(data["evaluations"]["total"], 2)
        self.assertEqual(data["evaluations"]["needs_support"], 1)
        self.assertEqual(data["evaluations"]["average_percentage"], 50)
        levels = {r["key"]: r["count"] for r in data["evaluations"]["by_level"]}
        self.assertEqual((levels["ALTO"], levels["ESTABLE"], levels["LEVE"]), (1, 1, 0))
        self.assertEqual(data["appointments"]["upcoming"], 1)
        self.assertEqual(data["emergency"]["total"], 1)
        self.assertEqual(data["monthly"]["registrations"][-1]["count"], 3)
        self.assertEqual(data["monthly"]["evaluations"][-1]["count"], 2)

    def test_ca4_solo_el_administrador(self):
        for user in (self.patient, self.psy):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(self.url).status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 401)
