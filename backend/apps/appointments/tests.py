"""
Sprint 3: OM3-14 Buscar psicólogos · OM3-15 Perfil · OM3-16 Disponibilidad · OM3-17 Reservar · OM3-18 Mis sesiones.
Ejecutar: python manage.py test apps.appointments
"""
from datetime import time, timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.professionals.models import PsychologistProfile

from .models import Appointment, Availability
from .slots import local_tz

User = get_user_model()
PASSWORD = "ClaveSegura#2026"


def make_psychologist(email, first="Andrés", last="Restrepo", verified=True, specialty="CLINICA", full_week=True):
    user = User.objects.create_user(email=email, password=PASSWORD, first_name=first, last_name=last,
                                    role=User.Role.PSICOLOGO, email_verified=True)
    PsychologistProfile.objects.create(
        user=user, specialty=specialty, years_experience=7, license_number=f"TP{user.pk:05d}",
        description="Acompaño a adultos con ansiedad desde un enfoque cognitivo-conductual.", is_verified=verified,
    )
    if full_week:
        # todos los días de 8:00 a 20:00 para que siempre haya horarios mañana
        Availability.objects.bulk_create(
            Availability(psychologist=user, weekday=d, start_time=time(8), end_time=time(20)) for d in range(7)
        )
    return user


def make_patient(email="ana@x.com"):
    return User.objects.create_user(email=email, password=PASSWORD, first_name="Ana", last_name="Ríos",
                                    email_verified=True)


class SprintThreeTestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.psy = make_psychologist("andres@x.com")
        self.patient = make_patient()
        self.client.force_authenticate(self.patient)

    def slots(self, psychologist=None, **params):
        url = reverse("appointments:slots", args=[(psychologist or self.psy).pk])
        return self.client.get(url, params)

    def first_slot(self):
        return self.slots().data["days"][0]["slots"][0]["start"]

    def book(self, start=None, psychologist=None, **extra):
        data = {"psychologist": (psychologist or self.psy).pk, "start": start or self.first_slot(), **extra}
        return self.client.post(reverse("appointments:appointment-list"), data, format="json")


# --------------------------------------------------------------- OM3-14 y OM3-15
class BuscarYPerfilTests(SprintThreeTestCase):
    def setUp(self):
        super().setUp()
        make_psychologist("lucia@x.com", "Lucía", "Gómez", specialty="INFANTIL")
        make_psychologist("pedro@x.com", "Pedro", "Pérez", verified=False)

    def test_om3_14_listado_muestra_solo_profesionales_disponibles_con_info_basica(self):
        response = self.client.get(reverse("professionals:directory"))
        names = [p["full_name"] for p in response.data]
        self.assertEqual(names, ["Andrés Restrepo", "Lucía Gómez"])  # Pedro no está verificado
        item = response.data[0]
        for field in ("avatar_url", "specialty_display", "years_experience", "description", "next_available"):
            self.assertIn(field, item)
        self.assertIsNotNone(item["next_available"])

    def test_om3_14_buscar_por_nombre_o_especialidad(self):
        by_name = self.client.get(reverse("professionals:directory"), {"q": "lucía"}).data
        self.assertEqual([p["first_name"] for p in by_name], ["Lucía"])
        by_specialty = self.client.get(reverse("professionals:directory"), {"q": "infantil"}).data
        self.assertEqual([p["first_name"] for p in by_specialty], ["Lucía"])
        self.assertEqual(self.client.get(reverse("professionals:directory"), {"q": "zzz"}).data, [])

    def test_om3_14_la_info_corresponde_al_perfil_registrado(self):
        PsychologistProfile.objects.filter(user=self.psy).update(description="Texto actualizado por el psicólogo.")
        item = self.client.get(reverse("professionals:directory-detail", args=[self.psy.pk])).data
        self.assertEqual(item["description"], "Texto actualizado por el psicólogo.")

    def test_om3_15_perfil_muestra_especialidad_experiencia_e_info_profesional(self):
        response = self.client.get(reverse("professionals:directory-detail", args=[self.psy.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["specialty_display"], "Psicología clínica")
        self.assertEqual(response.data["years_experience"], 7)
        self.assertIn("description", response.data)

    def test_om3_15_perfil_de_psicologo_no_verificado_no_existe(self):
        pedro = User.objects.get(email="pedro@x.com")
        self.assertEqual(self.client.get(reverse("professionals:directory-detail", args=[pedro.pk])).status_code, 404)

    def test_psicologo_sin_horario_no_tiene_proximo_horario(self):
        Availability.objects.filter(psychologist=self.psy).delete()
        item = self.client.get(reverse("professionals:directory-detail", args=[self.psy.pk])).data
        self.assertIsNone(item["next_available"])


# --------------------------------------------------------------------- OM3-16
class DisponibilidadTests(SprintThreeTestCase):
    def test_ca1_ca2_muestra_solo_horarios_futuros_y_libres(self):
        response = self.slots()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["session_minutes"], 60)
        now = timezone.now()
        starts = [s["start"] for day in response.data["days"] for s in day["slots"]]
        self.assertTrue(starts)
        from datetime import datetime

        self.assertTrue(all(datetime.fromisoformat(s) > now for s in starts))
        self.assertTrue(all(s.endswith("-05:00") for s in starts))  # hora de Colombia

    def test_ca3_un_horario_ocupado_no_se_puede_seleccionar(self):
        start = self.first_slot()
        self.book(start)
        self.client.force_authenticate(make_patient("otro@x.com"))
        response = self.book(start)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ya no está disponible", str(response.data["start"]))

    def test_horario_fuera_de_la_agenda_o_en_el_pasado(self):
        past = (timezone.now() - timedelta(days=1)).replace(minute=0, second=0, microsecond=0)
        self.assertEqual(self.book(past.isoformat()).status_code, 400)
        odd = self.first_slot().replace(":00:00", ":17:00")
        self.assertEqual(self.book(odd).status_code, 400)
        far = (timezone.now() + timedelta(days=60)).astimezone(local_tz()).replace(hour=9, minute=0, second=0, microsecond=0)
        self.assertEqual(self.book(far.isoformat()).status_code, 400)

    def test_parametros_from_y_days(self):
        tomorrow = (timezone.now().astimezone(local_tz()) + timedelta(days=1)).date()
        response = self.slots(**{"from": tomorrow.isoformat(), "days": 1})
        self.assertEqual([d["date"] for d in response.data["days"]], [tomorrow.isoformat()])
        self.assertEqual(len(response.data["days"][0]["slots"]), 12)  # 8:00 a 20:00 en sesiones de 1 hora
        self.assertEqual(self.slots(**{"from": "ayer"}).status_code, 400)

    def test_psicologo_inexistente_o_sin_verificar(self):
        unverified = make_psychologist("nv@x.com", verified=False)
        self.assertEqual(self.slots(unverified).status_code, 404)
        self.assertEqual(self.client.get(reverse("appointments:slots", args=[9999])).status_code, 404)


# --------------------------------------------------------------------- OM3-17
class ReservarCitaTests(SprintThreeTestCase):
    def test_ca1_a_ca5_reserva_confirmada_registrada_y_horario_deja_de_estar_disponible(self):
        start = self.first_slot()
        response = self.book(start, reason="  Quiero manejar mejor la ansiedad  ")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # CA3 confirma la reserva
        self.assertEqual(response.data["status"], "PROGRAMADA")
        self.assertEqual(response.data["start"], start)
        self.assertEqual(response.data["psychologist"]["full_name"], "Andrés Restrepo")
        self.assertEqual(response.data["reason"], "Quiero manejar mejor la ansiedad")
        appointment = Appointment.objects.get()  # CA4 queda registrada
        self.assertEqual(appointment.end - appointment.start, timedelta(minutes=60))
        remaining = [s["start"] for d in self.slots().data["days"] for s in d["slots"]]
        self.assertNotIn(start, remaining)  # CA5

    def test_ca1_ca2_psicologo_y_horario_obligatorios(self):
        response = self.client.post(reverse("appointments:appointment-list"), {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("psychologist", response.data)
        self.assertIn("start", response.data)

    def test_no_se_reserva_con_psicologo_no_verificado(self):
        unverified = make_psychologist("nv@x.com", verified=False)
        response = self.book(self.first_slot(), psychologist=unverified)
        self.assertIn("no está disponible", str(response.data["psychologist"]))

    def test_dos_reservas_simultaneas_solo_pasa_una(self):
        start = self.first_slot()
        Appointment.objects.create(patient=make_patient("b@x.com"), psychologist=self.psy,
                                   start=timezone.datetime.fromisoformat(start),
                                   end=timezone.datetime.fromisoformat(start) + timedelta(hours=1))
        with mock.patch("apps.appointments.serializers.is_available", return_value=True):
            response = self.book(start)
        self.assertEqual(response.status_code, 400)
        self.assertIn("acaba de ser reservado", str(response.data["start"]))

    def test_solo_pacientes_reservan(self):
        self.client.force_authenticate(self.psy)
        self.assertEqual(self.book(self.first_slot()).status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post(reverse("appointments:appointment-list"), {}).status_code, 401)


# --------------------------------------------------------------------- OM3-18
class MisSesionesTests(SprintThreeTestCase):
    def test_ca1_a_ca4_ve_sus_citas_con_fecha_hora_y_psicologo(self):
        self.book()
        response = self.client.get(reverse("appointments:appointment-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        item = response.data[0]
        self.assertIn("T", item["start"])  # fecha y hora
        self.assertEqual(item["psychologist"]["full_name"], "Andrés Restrepo")
        self.assertEqual(item["psychologist"]["specialty"], "Psicología clínica")

    def test_citas_pasadas_y_canceladas_van_al_historial(self):
        appointment_id = self.book().data["id"]
        past_start = timezone.now() - timedelta(days=3)
        old = Appointment.objects.create(patient=self.patient, psychologist=self.psy, start=past_start,
                                         end=past_start + timedelta(hours=1), status=Appointment.Status.REALIZADA)
        upcoming = [a["id"] for a in self.client.get(reverse("appointments:appointment-list")).data]
        past = [a["id"] for a in self.client.get(reverse("appointments:appointment-list"), {"scope": "past"}).data]
        everything = self.client.get(reverse("appointments:appointment-list"), {"scope": "all"}).data
        self.assertEqual(upcoming, [appointment_id])
        self.assertEqual(past, [old.id])
        self.assertEqual(len(everything), 2)
        self.assertIn("andres@x.com", str(old))

    def test_cada_paciente_ve_solo_sus_citas(self):
        appointment_id = self.book().data["id"]
        self.client.force_authenticate(make_patient("otra@x.com"))
        self.assertEqual(self.client.get(reverse("appointments:appointment-list")).data, [])
        detail = self.client.get(reverse("appointments:appointment-detail", args=[appointment_id]))
        self.assertEqual(detail.status_code, 404)

    def test_el_psicologo_ve_la_cita_en_su_agenda(self):
        appointment_id = self.book().data["id"]
        self.client.force_authenticate(self.psy)
        agenda = self.client.get(reverse("appointments:appointment-list")).data
        self.assertEqual(agenda[0]["patient"]["full_name"], "Ana Ríos")
        detail = self.client.get(reverse("appointments:appointment-detail", args=[appointment_id]))
        self.assertEqual(detail.status_code, 200)

    def test_admin_no_tiene_sesiones(self):
        admin = User.objects.create_superuser(email="admin@x.com", password=PASSWORD, first_name="A", last_name="B")
        self.client.force_authenticate(admin)
        self.assertEqual(self.client.get(reverse("appointments:appointment-list")).status_code, 403)


# ----------------------------------------------------- horario semanal del psicólogo
class HorarioSemanalTests(SprintThreeTestCase):
    url = reverse("appointments:my-availability")

    def test_psicologo_consulta_y_reemplaza_su_horario(self):
        self.client.force_authenticate(self.psy)
        self.assertEqual(len(self.client.get(self.url).data), 7)
        items = [{"weekday": 0, "start_time": "08:00", "end_time": "12:00"},
                 {"weekday": 0, "start_time": "14:00", "end_time": "16:00"}]
        response = self.client.put(self.url, {"items": items}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([i["weekday_display"] for i in response.data], ["Lunes", "Lunes"])
        self.assertEqual(Availability.objects.filter(psychologist=self.psy).count(), 2)
        self.assertEqual(str(Availability.objects.first()), "Lunes 08:00-12:00")

    def test_validaciones_del_horario(self):
        self.client.force_authenticate(self.psy)
        backwards = [{"weekday": 1, "start_time": "12:00", "end_time": "08:00"}]
        self.assertIn("anterior", str(self.client.put(self.url, {"items": backwards}, format="json").data))
        overlap = [{"weekday": 2, "start_time": "08:00", "end_time": "12:00"},
                   {"weekday": 2, "start_time": "11:00", "end_time": "13:00"}]
        self.assertIn("se cruzan", str(self.client.put(self.url, {"items": overlap}, format="json").data))

    def test_solo_el_psicologo_define_horario(self):
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_clean_del_modelo(self):
        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            Availability(psychologist=self.psy, weekday=0, start_time=time(10), end_time=time(9)).clean()
