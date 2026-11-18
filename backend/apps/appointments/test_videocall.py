"""OM3-20 Videollamada. Ejecutar: python manage.py test apps.appointments.test_videocall"""
from datetime import timedelta

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Appointment, CallRoom
from .tests import SprintThreeTestCase, make_patient

OFFER = "v=0 oferta-del-psicologo"
ANSWER = "v=0 respuesta-del-paciente"


class VideollamadaTests(SprintThreeTestCase):
    def setUp(self):
        super().setUp()
        start = timezone.now().replace(second=0, microsecond=0) - timedelta(minutes=5)  # sesión en curso
        self.appointment = Appointment.objects.create(
            patient=self.patient, psychologist=self.psy, start=start, end=start + timedelta(hours=1)
        )
        self.url = reverse("appointments:call", args=[self.appointment.pk])

    def signal(self, action, sdp="", user=None):
        if user:
            self.client.force_authenticate(user)
        return self.client.post(self.url, {"action": action, "sdp": sdp}, format="json")

    def test_ca1_ca4_accede_desde_su_sesion_y_la_sala_es_de_esa_cita(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["can_join"])
        self.assertEqual(response.data["appointment"]["id"], self.appointment.pk)
        self.assertEqual(response.data["appointment"]["psychologist"]["full_name"], "Andrés Restrepo")
        self.assertTrue(response.data["ice_servers"])
        listed = self.client.get(reverse("appointments:appointment-list")).data[0]
        self.assertIn("call_opens_at", listed)

    def test_ca2_ca3_se_establece_la_conexion_entre_psicologo_y_paciente(self):
        # el paciente entra primero y espera
        self.assertEqual(self.signal("join").status_code, 200)
        self.assertEqual(self.signal("answer", ANSWER).status_code, 400)  # aún no hay oferta
        # el psicólogo entra y envía su oferta
        self.signal("join", user=self.psy)
        state = self.signal("offer", OFFER).data
        self.assertEqual(state["offer"], OFFER)
        # el paciente responde: la conexión de audio y video queda establecida
        state = self.signal("answer", ANSWER, user=self.patient).data
        self.assertEqual(state["answer"], ANSWER)
        self.client.force_authenticate(self.psy)
        self.assertEqual(self.client.get(self.url).data["answer"], ANSWER)
        self.assertIsNotNone(CallRoom.objects.get().started_at)
        # al colgar el psicólogo se limpia la conexión
        state = self.signal("leave").data
        self.assertEqual((state["offer"], state["answer"]), ("", ""))
        self.assertIsNone(state["psychologist_joined_at"])

    def test_cada_quien_cumple_su_papel(self):
        self.assertEqual(self.signal("offer", OFFER).status_code, 400)  # paciente no ofrece
        self.signal("join", user=self.psy)
        self.assertEqual(self.signal("answer", ANSWER).status_code, 400)  # psicólogo no responde
        self.assertEqual(self.signal("offer").status_code, 400)  # falta la descripción
        self.assertEqual(self.signal("bailar").status_code, 400)
        self.signal("offer", OFFER)
        self.client.force_authenticate(self.patient)
        state = self.signal("leave").data
        self.assertIsNone(state["patient_joined_at"])
        self.assertIn(str(self.appointment.pk), str(CallRoom.objects.get()))

    def test_ca4_solo_los_participantes_de_la_sesion(self):
        self.client.force_authenticate(make_patient("intruso@x.com"))
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_no_se_entra_antes_de_tiempo_ni_a_sesiones_terminadas(self):
        later = timezone.now() + timedelta(days=2)
        future = Appointment.objects.create(patient=self.patient, psychologist=self.psy, start=later, end=later + timedelta(hours=1))
        url = reverse("appointments:call", args=[future.pk])
        state = self.client.get(url).data
        self.assertFalse(state["can_join"])
        self.assertEqual(state["ice_servers"], [])
        self.assertEqual(self.client.post(url, {"action": "join"}, format="json").status_code, 400)

        self.appointment.end = timezone.now() - timedelta(minutes=1)
        self.appointment.save()
        self.assertIn("terminó", self.client.get(self.url).data["reason"])
        self.appointment.status = Appointment.Status.CANCELADA
        self.appointment.save()
        self.assertIn("ya no está programada", self.client.get(self.url).data["reason"])

    @override_settings(VIDEOCALL_TURN_URLS=["turn:turn.example.com:3478"], VIDEOCALL_TURN_USERNAME="u", VIDEOCALL_TURN_CREDENTIAL="c")
    def test_servidor_turn_opcional(self):
        servers = self.client.get(self.url).data["ice_servers"]
        self.assertEqual(servers[-1]["username"], "u")
