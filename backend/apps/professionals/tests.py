"""OM3-21 Registro profesional. Ejecutar: python manage.py test apps.professionals"""
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import PsychologistProfile

User = get_user_model()
PASSWORD = "ClaveSegura#2026"


class ProfessionalTestCase(APITestCase):
    url = reverse("professionals:register")

    def setUp(self):
        cache.clear()

    def payload(self, **overrides):
        data = {
            "first_name": "Carlos",
            "last_name": "Mejía",
            "email": "Carlos.Mejia@Correo.com",
            "phone": "3105551234",
            "password": PASSWORD,
            "password_confirm": PASSWORD,
            "accept_privacy": True,
            "specialty": "CLINICA",
            "years_experience": 6,
            "experience": "Hospital San Vicente, consulta privada.",
            "license_number": "tp 123456",
            "university": "Universidad de Antioquia",
            "description": "Psicólogo clínico con enfoque cognitivo-conductual para adultos con ansiedad.",
        }
        data.update(overrides)
        return data

    def register(self, **overrides):
        return self.client.post(self.url, self.payload(**overrides), format="json")


class RegistroProfesionalTests(ProfessionalTestCase):
    def test_ca1_a_ca5_registro_completo(self):
        response = self.register()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "carlos.mejia@correo.com")
        self.assertIn("Confirma tu correo", mail.outbox[0].subject)  # verificación de correo
        profile = PsychologistProfile.objects.get(user__email="carlos.mejia@correo.com")
        self.assertEqual(profile.user.role, "PSICOLOGO")
        self.assertFalse(profile.is_verified)
        self.assertEqual(profile.specialty, "CLINICA")                      # CA2
        self.assertEqual(profile.years_experience, 6)                       # CA3
        self.assertEqual(profile.license_number, "TP123456")                # CA4 (normalizada)
        self.assertTrue(profile.description.startswith("Psicólogo"))       # CA5
        self.assertEqual(profile.get_specialty_display(), "Psicología clínica")

    def test_campos_profesionales_obligatorios(self):
        data = self.payload()
        for field in ("specialty", "years_experience", "license_number", "description"):
            data.pop(field)
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        for field in ("specialty", "years_experience", "license_number", "description"):
            self.assertIn(field, response.data)
        self.assertFalse(User.objects.exists())

    def test_ca2_especialidad_invalida(self):
        response = self.register(specialty="ASTROLOGIA")
        self.assertIn("especialidad válida", str(response.data["specialty"]))

    def test_ca3_experiencia_invalida(self):
        self.assertIn("negativos", str(self.register(years_experience=-1).data["years_experience"]))
        self.assertIn("máximo 60", str(self.register(years_experience=70).data["years_experience"]))

    def test_ca4_licencia_duplicada_o_invalida(self):
        self.register()
        response = self.register(email="otro@correo.com", license_number="TP-123456".replace("-", ""))
        self.assertIn("ya está registrada", str(response.data["license_number"]))
        response = self.register(email="otro2@correo.com", license_number="tp#1")
        self.assertIn("letras, números", str(response.data["license_number"]))

    def test_ca5_descripcion_muy_corta(self):
        response = self.register(description="Hola")
        self.assertIn("mínimo 30", str(response.data["description"]))

    def test_tambien_valida_datos_de_la_cuenta(self):
        self.register()
        response = self.register(license_number="TP999999")
        self.assertIn("aún no ha sido confirmado", str(response.data["email"]))

    def test_especialidades_disponibles(self):
        response = self.client.get(reverse("professionals:specialties"))
        self.assertEqual(response.status_code, 200)
        self.assertIn({"value": "CLINICA", "label": "Psicología clínica"}, response.data)


class PerfilYVerificacionTests(ProfessionalTestCase):
    def setUp(self):
        super().setUp()
        self.register()
        self.psychologist = User.objects.get(email="carlos.mejia@correo.com")
        self.admin = User.objects.create_superuser(email="admin@x.com", password=PASSWORD, first_name="A", last_name="B")

    def test_psicologo_consulta_y_edita_su_perfil(self):
        self.client.force_authenticate(self.psychologist)
        response = self.client.get(reverse("professionals:me"))
        self.assertEqual(response.data["license_number"], "TP123456")

        response = self.client.patch(reverse("professionals:me"), {"years_experience": 7, "specialty": "SALUD"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["years_experience"], 7)
        # puede conservar su propia tarjeta sin error de duplicado
        response = self.client.patch(reverse("professionals:me"), {"license_number": "TP123456"}, format="json")
        self.assertEqual(response.status_code, 200)

    def test_psicologo_no_puede_autoverificarse(self):
        self.client.force_authenticate(self.psychologist)
        self.client.patch(reverse("professionals:me"), {"is_verified": True}, format="json")
        self.assertFalse(PsychologistProfile.objects.get().is_verified)
        response = self.client.post(reverse("professionals:verify", args=[1]), {"is_verified": True}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_paciente_no_tiene_perfil_profesional(self):
        patient = User.objects.create_user(email="p@x.com", password=PASSWORD, first_name="P", last_name="Q")
        self.client.force_authenticate(patient)
        self.assertEqual(self.client.get(reverse("professionals:me")).status_code, 403)

    def test_admin_lista_y_verifica_profesionales(self):
        self.client.force_authenticate(self.admin)
        pending = self.client.get(reverse("professionals:list"), {"verified": "false"}).data
        self.assertEqual(len(pending), 1)

        profile_id = pending[0]["id"]
        response = self.client.post(reverse("professionals:verify", args=[profile_id]), {"is_verified": True}, format="json")
        self.assertTrue(response.data["is_verified"])
        self.assertIsNotNone(response.data["verified_at"])
        self.assertEqual(len(self.client.get(reverse("professionals:list"), {"verified": "true"}).data), 1)

        response = self.client.post(reverse("professionals:verify", args=[profile_id]), {"is_verified": False}, format="json")
        self.assertIsNone(response.data["verified_at"])

    def test_me_indica_si_esta_verificado(self):
        PsychologistProfile.objects.update(is_verified=True)
        self.client.force_authenticate(self.psychologist)
        self.assertTrue(self.client.get(reverse("accounts:me")).data["is_verified"])
        self.assertIn("TP123456", str(PsychologistProfile.objects.get()))


class DirectorioTests(ProfessionalTestCase):
    def setUp(self):
        super().setUp()
        self.register()
        self.register(email="pendiente@correo.com", license_number="TP777777", first_name="Pedro")
        PsychologistProfile.objects.filter(user__email="carlos.mejia@correo.com").update(is_verified=True)
        self.patient = User.objects.create_user(email="p@x.com", password=PASSWORD, first_name="P", last_name="Q")

    def test_paciente_ve_solo_psicologos_verificados_con_foto_y_descripcion(self):
        self.client.force_authenticate(self.patient)
        response = self.client.get(reverse("professionals:directory"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([p["full_name"] for p in response.data], ["Carlos Mejía"])
        item = response.data[0]
        self.assertIn("avatar_url", item)
        self.assertTrue(item["description"].startswith("Psicólogo clínico"))
        self.assertNotIn("license_number", item)  # datos internos no se muestran

        detail = self.client.get(reverse("professionals:directory-detail", args=[item["id"]]))
        self.assertEqual(detail.data["specialty_display"], "Psicología clínica")

    def test_filtrar_por_especialidad_y_requiere_sesion(self):
        self.client.force_authenticate(self.patient)
        self.assertEqual(self.client.get(reverse("professionals:directory"), {"specialty": "familia"}).data, [])
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(reverse("professionals:directory")).status_code, 401)


class GestionarPerfilProfesionalTests(APITestCase):
    """OM3-22 Gestionar perfil profesional."""

    def setUp(self):
        self.psychologist = User.objects.create_user(
            email="psi@x.com", password=PASSWORD, first_name="Laura", last_name="Mesa", role=User.Role.PSICOLOGO,
        )
        PsychologistProfile.objects.create(
            user=self.psychologist, specialty="CLINICA", years_experience=4, license_number="TP-1111",
            description="Acompaño procesos de ansiedad y estrés en adultos jóvenes.", is_verified=True,
        )
        self.client.force_authenticate(self.psychologist)
        self.url = reverse("professionals:me")

    def test_ca1_consulta_su_informacion(self):
        data = self.client.get(self.url).data
        for field in ("first_name", "last_name", "phone", "specialty", "years_experience", "description", "license_number"):
            self.assertIn(field, data)
        self.assertEqual(data["user"]["email"], "psi@x.com")

    def test_ca2_ca3_modifica_los_datos_permitidos_y_se_guardan(self):
        changes = {"first_name": " Laura Sofía ", "phone": "300 123 4567", "years_experience": 5,
                   "university": "Universidad de Medellín", "description": "Nueva descripción de mi enfoque terapéutico."}
        response = self.client.patch(self.url, changes, format="json")
        self.assertEqual(response.status_code, 200)
        self.psychologist.refresh_from_db()
        profile = self.psychologist.psychologist_profile
        self.assertEqual(self.psychologist.first_name, "Laura Sofía")
        self.assertEqual(self.psychologist.phone, "300 123 4567")
        self.assertEqual((profile.years_experience, profile.university), (5, "Universidad de Medellín"))

    def test_ca2_datos_no_permitidos_no_cambian(self):
        self.client.patch(self.url, {"license_number": "TP-9999", "is_verified": False}, format="json")
        profile = PsychologistProfile.objects.get()
        self.assertEqual(profile.license_number, "TP-1111")
        self.assertTrue(profile.is_verified)

    def test_validaciones(self):
        response = self.client.patch(self.url, {"first_name": "  ", "phone": "abc", "years_experience": -1, "description": "corta"}, format="json")
        self.assertEqual(response.status_code, 400)
        for field in ("first_name", "phone", "years_experience", "description"):
            self.assertIn(field, response.data)
        self.assertIn("last_name", self.client.patch(self.url, {"last_name": ""}, format="json").data)

    def test_ca4_la_informacion_actualizada_se_muestra_en_su_perfil(self):
        self.client.patch(self.url, {"last_name": "Mesa Ríos", "specialty": "SALUD"}, format="json")
        mine = self.client.get(self.url).data
        self.assertEqual(mine["user"]["full_name"], "Laura Mesa Ríos")
        public = self.client.get(reverse("professionals:directory-detail", args=[self.psychologist.pk])).data
        self.assertEqual(public["full_name"], "Laura Mesa Ríos")
        self.assertEqual(public["specialty"], "SALUD")
