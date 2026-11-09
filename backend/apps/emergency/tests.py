"""OM3-19 Chat de emergencia. Ejecutar: python manage.py test apps.emergency"""
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.professionals.models import PsychologistProfile

from .models import EmergencyChat, Message

User = get_user_model()
PASSWORD = "ClaveSegura#2026"


def make_user(email, role=User.Role.PACIENTE, verified=None):
    user = User.objects.create_user(email=email, password=PASSWORD, first_name=email.split("@")[0].title(),
                                    last_name="Prueba", role=role)
    if verified is not None:
        PsychologistProfile.objects.create(
            user=user, specialty="CLINICA", years_experience=5, license_number=f"TP{user.pk:04d}",
            description="Descripción profesional suficientemente larga.", is_verified=verified,
        )
    return user


class ChatTestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.patient = make_user("ana@openmind.com")
        self.other_patient = make_user("beto@openmind.com")
        self.psy = make_user("psico@openmind.com", User.Role.PSICOLOGO, verified=True)
        self.psy2 = make_user("psico2@openmind.com", User.Role.PSICOLOGO, verified=True)

    def as_user(self, user):
        self.client.force_authenticate(user)

    def open_chat(self):
        self.as_user(self.patient)
        return self.client.post(reverse("emergency:chat-list"))

    def messages_url(self, chat_id):
        return reverse("emergency:chat-messages", args=[chat_id])


class ChatPacienteTests(ChatTestCase):
    def test_ca5_informacion_clara_del_servicio(self):
        response = self.client.get(reverse("emergency:info"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("description", response.data)
        self.assertIn("123", [line["phone"] for line in response.data["lines"]])
        self.assertIn("no reemplaza", response.data["disclaimer"])

    def test_ca1_paciente_inicia_el_chat_con_mensaje_de_bienvenida(self):
        response = self.open_chat()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "ESPERANDO")
        self.assertIn("Hola Ana", response.data["last_message"]["text"])
        self.assertTrue(response.data["last_message"]["is_system"])

    def test_si_ya_tiene_un_chat_abierto_lo_retoma(self):
        first = self.open_chat().data["id"]
        response = self.open_chat()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], first)
        self.assertEqual(EmergencyChat.objects.count(), 1)

    def test_ca2_ca3_enviar_y_ver_mensajes(self):
        chat_id = self.open_chat().data["id"]
        response = self.client.post(self.messages_url(chat_id), {"text": "  Me siento muy ansiosa  "}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["text"], "Me siento muy ansiosa")
        self.assertTrue(response.data["is_mine"])

        messages = self.client.get(self.messages_url(chat_id)).data
        self.assertEqual(len(messages), 2)  # bienvenida + mensaje

    def test_mensaje_vacio(self):
        chat_id = self.open_chat().data["id"]
        response = self.client.post(self.messages_url(chat_id), {"text": "   "}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data["text"][0]), "Escribe un mensaje.")

    def test_ca4_conversacion_asociada_solo_a_su_paciente(self):
        chat_id = self.open_chat().data["id"]
        self.as_user(self.other_patient)
        self.assertEqual(self.client.get(reverse("emergency:chat-list")).data, [])
        self.assertEqual(self.client.get(self.messages_url(chat_id)).status_code, 404)
        response = self.client.post(self.messages_url(chat_id), {"text": "hola"}, format="json")
        self.assertEqual(response.status_code, 404)

    def test_paciente_ve_sus_chats_anteriores(self):
        chat_id = self.open_chat().data["id"]
        self.client.post(reverse("emergency:chat-close", args=[chat_id]))
        response = self.client.get(reverse("emergency:chat-list"), {"status": "cerrada"})
        self.assertEqual(len(response.data), 1)

    def test_no_se_escribe_en_un_chat_cerrado(self):
        chat_id = self.open_chat().data["id"]
        response = self.client.post(reverse("emergency:chat-close", args=[chat_id]))
        self.assertEqual(response.data["status"], "CERRADA")
        response = self.client.post(self.messages_url(chat_id), {"text": "hola"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # cerrar de nuevo no falla
        self.assertEqual(self.client.post(reverse("emergency:chat-close", args=[chat_id])).status_code, 200)
        # puede abrir uno nuevo
        self.assertEqual(self.open_chat().status_code, status.HTTP_201_CREATED)

    def test_admin_no_accede_al_chat(self):
        admin = User.objects.create_superuser(email="admin@x.com", password=PASSWORD, first_name="A", last_name="B")
        self.as_user(admin)
        self.assertEqual(self.client.get(reverse("emergency:chat-list")).status_code, 403)


class ChatPsicologoTests(ChatTestCase):
    def test_psicologo_ve_la_fila_toma_el_chat_y_responde(self):
        chat_id = self.open_chat().data["id"]
        self.client.post(self.messages_url(chat_id), {"text": "Necesito ayuda"}, format="json")

        self.as_user(self.psy)
        queue = self.client.get(reverse("emergency:chat-list"), {"status": "ESPERANDO"}).data
        self.assertEqual([c["id"] for c in queue], [chat_id])

        # no puede escribir antes de tomarlo
        response = self.client.post(self.messages_url(chat_id), {"text": "hola"}, format="json")
        self.assertEqual(response.status_code, 403)

        response = self.client.post(reverse("emergency:chat-take", args=[chat_id]))
        self.assertEqual(response.data["status"], "ACTIVA")
        self.assertEqual(response.data["psychologist"]["specialty"], "Psicología clínica")

        self.client.post(self.messages_url(chat_id), {"text": "Hola Ana, aquí estoy."}, format="json")

        # el paciente ve los mensajes recibidos (CA3) y puede pedir solo los nuevos
        self.as_user(self.patient)
        messages = self.client.get(self.messages_url(chat_id)).data
        self.assertEqual(messages[-1]["sender_name"], "Psico Prueba")
        self.assertFalse(messages[-1]["is_mine"])
        new = self.client.get(self.messages_url(chat_id), {"after": messages[-2]["id"]}).data
        self.assertEqual(len(new), 1)

    def test_otro_psicologo_no_puede_tomar_un_chat_ya_tomado(self):
        chat_id = self.open_chat().data["id"]
        self.as_user(self.psy)
        self.client.post(reverse("emergency:chat-take", args=[chat_id]))
        self.as_user(self.psy2)
        # ya no aparece en su fila ni puede verlo
        self.assertEqual(self.client.get(reverse("emergency:chat-list")).data, [])
        self.assertEqual(self.client.post(reverse("emergency:chat-take", args=[chat_id])).status_code, 404)

    def test_tomar_chat_cerrado(self):
        chat_id = self.open_chat().data["id"]
        self.as_user(self.psy)
        self.client.post(reverse("emergency:chat-take", args=[chat_id]))
        self.client.post(reverse("emergency:chat-close", args=[chat_id]))
        response = self.client.post(reverse("emergency:chat-take", args=[chat_id]))
        self.assertEqual(response.status_code, 400)

    def test_psicologo_sin_verificar_no_atiende(self):
        unverified = make_user("nuevo@openmind.com", User.Role.PSICOLOGO, verified=False)
        self.as_user(unverified)
        response = self.client.get(reverse("emergency:chat-list"))
        self.assertEqual(response.status_code, 403)
        self.assertIn("verificado", response.data["detail"])

    def test_psicologo_no_inicia_chats_ni_paciente_toma(self):
        self.as_user(self.psy)
        self.assertEqual(self.client.post(reverse("emergency:chat-list")).status_code, 403)
        chat_id = self.open_chat().data["id"]
        self.assertEqual(self.client.post(reverse("emergency:chat-take", args=[chat_id])).status_code, 403)

    def test_solo_participantes_cierran(self):
        chat_id = self.open_chat().data["id"]
        self.as_user(self.psy)
        # lo puede ver en la fila, pero no cerrarlo sin tomarlo
        self.assertEqual(self.client.post(reverse("emergency:chat-close", args=[chat_id])).status_code, 403)

    def test_representacion_de_modelos(self):
        chat_id = self.open_chat().data["id"]
        chat = EmergencyChat.objects.get(pk=chat_id)
        self.assertIn("Esperando psicólogo", str(chat))
        self.assertTrue(str(Message.objects.first()).startswith("Sistema:"))
