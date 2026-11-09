"""
Pruebas del Sprint 1 (Gestión de usuarios).
Cada clase corresponde a una historia de Jira y cada prueba indica el criterio que valida.

Ejecutar:  python manage.py test
"""
import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

PASSWORD = "ClaveSegura#2026"
NEW_PASSWORD = "NuevaClave#2026"


class BaseTestCase(APITestCase):
    def setUp(self):
        cache.clear()  # reinicia los límites de intentos (throttling)

    def make_user(self, email="paciente@openmind.com", role=User.Role.PACIENTE, **extra):
        extra.setdefault("email_verified", True)
        return User.objects.create_user(
            email=email, password=PASSWORD, first_name="Laura", last_name="Ríos", role=role, **extra
        )

    def verification_token(self):
        """Saca el token del enlace que llegó en el último correo de verificación."""
        return re.search(r"verificar-correo\?token=([\w:.-]+)", mail.outbox[-1].body).group(1)

    def login(self, email, password=PASSWORD):
        return self.client.post(reverse("accounts:login"), {"email": email, "password": password}, format="json")


# ----------------------------------------------------------------- OM3-9 Registro
class RegisterTests(BaseTestCase):
    url = reverse("accounts:register")

    def payload(self, **overrides):
        data = {
            "email": "Ana.Gomez@Correo.com",
            "first_name": "Ana",
            "last_name": "Gómez",
            "phone": "3001234567",
            "birth_date": "2000-05-14",
            "password": PASSWORD,
            "password_confirm": PASSWORD,
        }
        data.update(overrides)
        return data

    def test_ca1_registro_crea_paciente_sin_verificar_y_envia_correo(self):
        response = self.client.post(self.url, self.payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "ana.gomez@correo.com")
        self.assertNotIn("access", response.data)  # todavía no puede entrar
        user = User.objects.get(email="ana.gomez@correo.com")
        self.assertEqual(user.role, "PACIENTE")
        self.assertFalse(user.email_verified)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertEqual(mail.outbox[0].to, ["ana.gomez@correo.com"])
        self.assertIn("Confirma tu correo", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].alternatives[0][1], "text/html")

    def test_ca5_al_confirmar_el_correo_accede_a_su_cuenta(self):
        self.client.post(self.url, self.payload(), format="json")
        # antes de confirmar, el login se bloquea con un código para reenviar el correo
        response = self.login("ana.gomez@correo.com")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["code"], "email_not_verified")

        response = self.client.post(reverse("accounts:verify-email"), {"token": self.verification_token()}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(User.objects.get(email="ana.gomez@correo.com").email_verified)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        response = self.client.get(reverse("accounts:me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "ana.gomez@correo.com")
        self.assertEqual(self.login("ana.gomez@correo.com").status_code, status.HTTP_200_OK)

    def test_si_el_correo_no_se_puede_enviar_no_se_crea_la_cuenta(self):
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend", EMAIL_PORT=1):
            response = self.client.post(self.url, self.payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertFalse(User.objects.exists())

    def test_correo_registrado_sin_confirmar(self):
        self.client.post(self.url, self.payload(), format="json")
        response = self.client.post(self.url, self.payload(), format="json")
        self.assertIn("aún no ha sido confirmado", str(response.data["email"][0]))

    def test_contrasena_se_guarda_encriptada(self):
        self.client.post(self.url, self.payload(), format="json")
        user = User.objects.get(email="ana.gomez@correo.com")
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.password.startswith("pbkdf2_sha256$"))

    def test_ca2_campos_obligatorios_vacios(self):
        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        for field in ("email", "first_name", "last_name", "password", "password_confirm"):
            self.assertIn(field, response.data)
            self.assertEqual(str(response.data[field][0]), "Este campo es obligatorio.")

    def test_ca2_campos_en_blanco(self):
        response = self.client.post(self.url, self.payload(first_name="", last_name=""), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("first_name", response.data)
        self.assertIn("last_name", response.data)

    def test_campos_opcionales_pueden_omitirse(self):
        data = self.payload()
        data.pop("phone")
        data.pop("birth_date")
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_ca3_correo_con_formato_invalido(self):
        for bad_email in ("ana", "ana@", "ana@correo", "@correo.com"):
            response = self.client.post(self.url, self.payload(email=bad_email), format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, bad_email)
            self.assertIn("email", response.data)

    def test_ca4_correo_ya_registrado_sin_importar_mayusculas(self):
        self.make_user(email="ana.gomez@correo.com")
        response = self.client.post(self.url, self.payload(email="ANA.GOMEZ@correo.com"), format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ya se encuentra registrado", str(response.data["email"][0]))

    def test_contrasenas_no_coinciden(self):
        response = self.client.post(self.url, self.payload(password_confirm="OtraClave#2026"), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data)

    def test_contrasena_debil(self):
        response = self.client.post(self.url, self.payload(password="12345678", password_confirm="12345678"), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_telefono_invalido(self):
        response = self.client.post(self.url, self.payload(phone="abc"), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone", response.data)

    def test_no_se_puede_autoasignar_otro_rol(self):
        response = self.client.post(self.url, self.payload(role="ADMINISTRADOR"), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.get().role, "PACIENTE")


# --------------------------------------------------------- OM3-10 Inicio de sesión
class LoginTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.paciente = self.make_user()
        self.psicologo = self.make_user(email="psicologo@openmind.com", role=User.Role.PSICOLOGO)
        self.admin = User.objects.create_superuser(
            email="admin@openmind.com", password=PASSWORD, first_name="Admin", last_name="OpenMind"
        )

    def test_ca1_correo_y_contrasena_son_obligatorios(self):
        response = self.client.post(reverse("accounts:login"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertIn("password", response.data)

    def test_ca2_ca3_credenciales_correctas_permiten_acceso(self):
        response = self.login("PACIENTE@openmind.com")  # el correo no distingue mayúsculas

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_ca4_contrasena_incorrecta_muestra_error(self):
        response = self.login("paciente@openmind.com", "incorrecta")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Correo o contraseña incorrectos.")

    def test_ca4_correo_inexistente_muestra_el_mismo_error(self):
        response = self.login("nadie@openmind.com")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Correo o contraseña incorrectos.")

    def test_usuario_inactivo_no_puede_ingresar(self):
        self.paciente.is_active = False
        self.paciente.save()
        response = self.login("paciente@openmind.com")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ca5_identifica_el_tipo_de_usuario(self):
        expected = {
            "paciente@openmind.com": "PACIENTE",
            "psicologo@openmind.com": "PSICOLOGO",
            "admin@openmind.com": "ADMINISTRADOR",
        }
        for email, role in expected.items():
            response = self.login(email)
            self.assertEqual(response.data["user"]["role"], role)

    def test_me_requiere_autenticacion(self):
        self.assertEqual(self.client.get(reverse("accounts:me")).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_renueva_el_access(self):
        refresh = self.login("paciente@openmind.com").data["refresh"]
        response = self.client.post(reverse("accounts:refresh"), {"refresh": refresh}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_logout_invalida_el_refresh(self):
        tokens = self.login("paciente@openmind.com").data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        response = self.client.post(reverse("accounts:logout"), {"refresh": tokens["refresh"]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        response = self.client.post(reverse("accounts:refresh"), {"refresh": tokens["refresh"]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_con_token_invalido(self):
        tokens = self.login("paciente@openmind.com").data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = self.client.post(reverse("accounts:logout"), {"refresh": "no-es-un-token"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_control_de_roles_solo_admin_lista_usuarios(self):
        for email, expected_status in (
            ("paciente@openmind.com", status.HTTP_403_FORBIDDEN),
            ("psicologo@openmind.com", status.HTTP_403_FORBIDDEN),
            ("admin@openmind.com", status.HTTP_200_OK),
        ):
            access = self.login(email).data["access"]
            self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
            response = self.client.get(reverse("accounts:users"))
            self.assertEqual(response.status_code, expected_status, email)

    def test_admin_filtra_usuarios_por_rol(self):
        access = self.login("admin@openmind.com").data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.get(reverse("accounts:users"), {"role": "psicologo"})
        self.assertEqual([u["email"] for u in response.data], ["psicologo@openmind.com"])

    def test_bloquea_demasiados_intentos(self):
        for _ in range(10):
            self.login("paciente@openmind.com", "incorrecta")
        response = self.login("paciente@openmind.com", "incorrecta")
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


# ------------------------------------------------- OM3-11 Recuperación de contraseña
class PasswordResetTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.make_user()

    def request_reset(self, email="paciente@openmind.com"):
        return self.client.post(reverse("accounts:password-reset"), {"email": email}, format="json")

    def get_link_params(self):
        """Saca uid y token del enlace que llegó en el correo."""
        match = re.search(r"uid=([\w-]+)&token=([\w-]+)", mail.outbox[-1].body)
        return {"uid": match.group(1), "token": match.group(2)}

    def test_ca1_ca3_solicitud_envia_correo_con_instrucciones(self):
        response = self.request_reset("Paciente@OpenMind.com")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ["paciente@openmind.com"])
        self.assertIn("Recupera tu contraseña", email.subject)
        self.assertIn("/restablecer-contrasena?uid=", email.body)
        self.assertEqual(email.alternatives[0][1], "text/html")

    def test_ca2_correo_no_registrado(self):
        response = self.request_reset("noexiste@openmind.com")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("No encontramos", response.data["detail"])
        self.assertEqual(len(mail.outbox), 0)

    def test_correo_con_formato_invalido(self):
        response = self.request_reset("no-es-correo")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_error_al_enviar_el_correo(self):
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend", EMAIL_PORT=1):
            response = self.request_reset()
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_validar_enlace_vigente(self):
        self.request_reset()
        response = self.client.post(reverse("accounts:password-reset-validate"), self.get_link_params(), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_restablecer_contrasena_tambien_confirma_el_correo(self):
        self.user.email_verified = False
        self.user.save()
        self.request_reset()
        data = {**self.get_link_params(), "password": NEW_PASSWORD, "password_confirm": NEW_PASSWORD}
        self.client.post(reverse("accounts:password-reset-confirm"), data, format="json")
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

    def test_ca4_establece_nueva_contrasena_y_puede_ingresar(self):
        self.request_reset()
        data = {**self.get_link_params(), "password": NEW_PASSWORD, "password_confirm": NEW_PASSWORD}

        response = self.client.post(reverse("accounts:password-reset-confirm"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(self.login("paciente@openmind.com", PASSWORD).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.login("paciente@openmind.com", NEW_PASSWORD).status_code, status.HTTP_200_OK)

    def test_el_enlace_solo_sirve_una_vez(self):
        self.request_reset()
        params = self.get_link_params()
        data = {**params, "password": NEW_PASSWORD, "password_confirm": NEW_PASSWORD}
        self.client.post(reverse("accounts:password-reset-confirm"), data, format="json")

        data = {**params, "password": "OtraMas#2026", "password_confirm": "OtraMas#2026"}
        response = self.client.post(reverse("accounts:password-reset-confirm"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    def test_token_invalido(self):
        self.request_reset()
        params = {**self.get_link_params(), "token": "token-falso"}
        response = self.client.post(reverse("accounts:password-reset-validate"), params, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_uid_invalido(self):
        response = self.client.post(
            reverse("accounts:password-reset-validate"), {"uid": "@@@", "token": "x"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nuevas_contrasenas_no_coinciden(self):
        self.request_reset()
        data = {**self.get_link_params(), "password": NEW_PASSWORD, "password_confirm": "Diferente#2026"}
        response = self.client.post(reverse("accounts:password-reset-confirm"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data)

    def test_nueva_contrasena_debil(self):
        self.request_reset()
        data = {**self.get_link_params(), "password": "123", "password_confirm": "123"}
        response = self.client.post(reverse("accounts:password-reset-confirm"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)


# ------------------------------------------------------------ Verificación de correo
class EmailVerificationTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.make_user(email="nuevo@openmind.com", email_verified=False)

    def resend(self, email="nuevo@openmind.com"):
        return self.client.post(reverse("accounts:verify-email-resend"), {"email": email}, format="json")

    def verify(self, token):
        return self.client.post(reverse("accounts:verify-email"), {"token": token}, format="json")

    def test_reenviar_enlace_y_verificar(self):
        response = self.resend("NUEVO@openmind.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        response = self.verify(self.verification_token())
        self.assertEqual(response.data["user"]["email_verified"], True)

    def test_el_enlace_puede_abrirse_de_nuevo_sin_error(self):
        self.resend()
        token = self.verification_token()
        self.verify(token)
        self.assertEqual(self.verify(token).status_code, status.HTTP_200_OK)

    def test_reenviar_a_cuenta_ya_verificada_o_inexistente(self):
        self.user.email_verified = True
        self.user.save()
        self.assertIn("ya está confirmado", self.resend().data["detail"])
        self.assertEqual(self.resend("nadie@x.com").status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(len(mail.outbox), 0)

    def test_reenviar_con_error_de_correo(self):
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend", EMAIL_PORT=1):
            self.assertEqual(self.resend().status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_token_invalido_o_vencido(self):
        self.assertIn("no es válido", str(self.verify("abc").data["token"]))
        self.resend()
        token = self.verification_token()
        with self.settings(EMAIL_VERIFICATION_HOURS=0):
            import time
            time.sleep(1)
            self.assertIn("expiró", str(self.verify(token).data["token"]))

    def test_token_de_usuario_eliminado(self):
        self.resend()
        token = self.verification_token()
        self.user.delete()
        self.assertIn("no es válido", str(self.verify(token).data["token"]))

    def test_token_no_sirve_si_cambio_el_correo(self):
        self.resend()
        token = self.verification_token()
        self.user.email = "otro@openmind.com"
        self.user.save()
        self.assertEqual(self.verify(token).status_code, status.HTTP_400_BAD_REQUEST)


class BrevoBackendTests(BaseTestCase):
    def test_envia_por_la_api_http_de_brevo(self):
        from unittest import mock

        from django.core.mail import EmailMultiAlternatives

        from .email_backends import BREVO_URL, BrevoEmailBackend

        message = EmailMultiAlternatives("Asunto", "Texto", "OpenMind <hola@openmind.app>", ["Ana <ana@x.com>"])
        message.attach_alternative("<p>HTML</p>", "text/html")
        with self.settings(BREVO_API_KEY="clave"), mock.patch("urllib.request.urlopen") as urlopen:
            sent = BrevoEmailBackend().send_messages([message])
        self.assertEqual(sent, 1)
        request = urlopen.call_args[0][0]
        self.assertEqual(request.full_url, BREVO_URL)
        self.assertEqual(request.get_header("Api-key"), "clave")
        import json

        payload = json.loads(request.data)
        self.assertEqual(payload["sender"], {"email": "hola@openmind.app", "name": "OpenMind"})
        self.assertEqual(payload["to"], [{"email": "ana@x.com"}])
        self.assertEqual(payload["htmlContent"], "<p>HTML</p>")

    def test_errores_de_brevo(self):
        from unittest import mock

        from django.core.exceptions import ImproperlyConfigured
        from django.core.mail import EmailMessage

        from .email_backends import BrevoEmailBackend

        with self.settings(BREVO_API_KEY=""):
            with self.assertRaises(ImproperlyConfigured):
                BrevoEmailBackend()
        message = EmailMessage("Asunto", "Texto", "hola@openmind.app", ["ana@x.com"])
        with self.settings(BREVO_API_KEY="clave"), mock.patch("urllib.request.urlopen", side_effect=OSError("red")), \
                self.assertLogs("apps.accounts.email_backends", "ERROR"):
            with self.assertRaises(OSError):
                BrevoEmailBackend().send_messages([message])
            self.assertEqual(BrevoEmailBackend(fail_silently=True).send_messages([message]), 0)


class ModelAndDocsTests(BaseTestCase):
    def test_superusuario_es_administrador(self):
        admin = User.objects.create_superuser(email="ADMIN@x.com", password=PASSWORD, first_name="A", last_name="B")
        self.assertEqual(admin.role, User.Role.ADMINISTRADOR)
        self.assertEqual(admin.email, "admin@x.com")
        self.assertIn("ADMINISTRADOR", str(admin))

    def test_crear_usuario_sin_correo_falla(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password=PASSWORD)

    def test_superusuario_requiere_flags(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(email="a@x.com", password=PASSWORD, is_staff=False)
        with self.assertRaises(ValueError):
            User.objects.create_superuser(email="b@x.com", password=PASSWORD, is_superuser=False)

    def test_portada_y_documentacion_disponibles(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/api/docs/").status_code, 200)
        self.assertEqual(self.client.get("/api/schema/").status_code, 200)


class SeedCommandTests(BaseTestCase):
    def test_seed_users_crea_un_usuario_por_rol(self):
        from io import StringIO

        from django.core.management import call_command

        call_command("seed_users", stdout=StringIO())
        call_command("seed_users", stdout=StringIO())  # la segunda vez no duplica
        self.assertEqual(User.objects.count(), 5)
        self.assertTrue(User.objects.get(email="admin@openmind.com").is_superuser)
        psychologist = User.objects.get(email="psicologo@openmind.com")
        self.assertTrue(psychologist.psychologist_profile.is_verified)
        self.assertEqual(User.objects.get(email="paciente@openmind.com").evaluations.count(), 4)
