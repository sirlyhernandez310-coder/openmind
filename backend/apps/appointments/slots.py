"""
Cálculo de horarios disponibles (OM3-16).

Cada psicólogo define franjas semanales (Availability). Se parten en sesiones de
APPOINTMENT_MINUTES minutos y se quitan las que ya pasaron o ya están reservadas.
"""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone

from .models import Appointment


def local_tz():
    return ZoneInfo(settings.TIME_ZONE)


def session_length():
    return timedelta(minutes=settings.APPOINTMENT_MINUTES)


def candidate_slots(psychologist, start_date: date, days: int):
    """Todos los inicios de sesión según el horario semanal, sin filtrar ocupados."""
    tz = local_tz()
    length = session_length()
    rules = list(psychologist.availabilities.all())
    for offset in range(days):
        day = start_date + timedelta(days=offset)
        for rule in rules:
            if rule.weekday != day.weekday():
                continue
            cursor = datetime.combine(day, rule.start_time, tzinfo=tz)
            limit = datetime.combine(day, rule.end_time, tzinfo=tz)
            while cursor + length <= limit:
                yield cursor
                cursor += length


def available_slots(psychologist, start_date: date | None = None, days: int | None = None):
    """Solo horarios futuros y libres, ordenados (CA2 de OM3-16)."""
    tz = local_tz()
    now = timezone.now()
    earliest = now + timedelta(minutes=settings.APPOINTMENT_MIN_NOTICE_MINUTES)
    days = days or settings.APPOINTMENT_DAYS_AHEAD
    start_date = start_date or now.astimezone(tz).date()

    taken = set(
        Appointment.objects.filter(
            psychologist=psychologist,
            status=Appointment.Status.PROGRAMADA,
            start__date__gte=start_date - timedelta(days=1),
        ).values_list("start", flat=True)
    )
    slots = sorted({s for s in candidate_slots(psychologist, start_date, days) if s >= earliest and s not in taken})
    return slots


def is_available(psychologist, start):
    """Verifica en el servidor que un horario concreto se pueda reservar (CA3 de OM3-16)."""
    local = start.astimezone(local_tz())
    days = (local.date() - timezone.now().astimezone(local_tz()).date()).days
    if days < 0 or days >= settings.APPOINTMENT_DAYS_AHEAD:
        return False
    return start in set(available_slots(psychologist))


def group_by_day(slots):
    length = session_length()
    days = {}
    for start in slots:
        local = start.astimezone(local_tz())
        days.setdefault(local.date(), []).append({"start": local.isoformat(), "end": (local + length).isoformat()})
    return [{"date": day.isoformat(), "slots": items} for day, items in days.items()]
