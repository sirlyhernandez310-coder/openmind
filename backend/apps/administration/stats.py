"""OM3-25: estadísticas generales calculadas directamente desde la base de datos."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.appointments.models import Appointment
from apps.emergency.models import EmergencyChat
from apps.evaluations.models import Evaluation, Level
from apps.professionals.models import PsychologistProfile

User = get_user_model()
MONTHS = 6


def counts_by(queryset, field, choices):
    found = dict(queryset.values_list(field).annotate(n=Count("pk")).order_by())
    return [{"key": value, "label": label, "count": found.get(value, 0)} for value, label in choices]


def month_starts(months=MONTHS):
    """Primer día de cada uno de los últimos `months` meses (hora local), del más antiguo al actual."""
    today = timezone.localdate()
    year, month = today.year, today.month
    starts = []
    for _ in range(months):
        starts.append((year, month))
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    return list(reversed(starts))


def monthly(queryset, date_field):
    first_year, first_month = month_starts()[0]
    start = timezone.make_aware(timezone.datetime(first_year, first_month, 1))
    rows = (
        queryset.filter(**{f"{date_field}__gte": start})
        .annotate(month=TruncMonth(date_field))
        .values("month")
        .annotate(n=Count("pk"))
        .order_by()
    )
    found = {(row["month"].year, row["month"].month): row["n"] for row in rows}
    return [{"month": f"{y}-{m:02d}", "count": found.get((y, m), 0)} for y, m in month_starts()]


def platform_stats():
    now = timezone.now()
    last_30 = now - timedelta(days=30)
    evaluations = Evaluation.objects.all()
    appointments = Appointment.objects.all()
    return {
        "generated_at": now,
        "users": {
            "total": User.objects.count(),
            "active": User.objects.filter(is_active=True).count(),
            "inactive": User.objects.filter(is_active=False).count(),
            "new_last_30_days": User.objects.filter(date_joined__gte=last_30).count(),
            "by_role": counts_by(User.objects.all(), "role", User.Role.choices),
        },
        "psychologists": {
            "verified": PsychologistProfile.objects.filter(is_verified=True).count(),
            "pending": PsychologistProfile.objects.filter(is_verified=False).count(),
        },
        "evaluations": {
            "total": evaluations.count(),
            "last_30_days": evaluations.filter(created_at__gte=last_30).count(),
            "needs_support": evaluations.filter(needs_support=True).count(),
            "average_percentage": round(evaluations.aggregate(v=Avg("percentage"))["v"] or 0),
            "by_level": counts_by(evaluations, "level", Level.choices),
        },
        "appointments": {
            "total": appointments.count(),
            "upcoming": appointments.filter(status=Appointment.Status.PROGRAMADA, end__gte=now).count(),
            "by_status": counts_by(appointments, "status", Appointment.Status.choices),
        },
        "emergency": {
            "total": EmergencyChat.objects.count(),
            "by_status": counts_by(EmergencyChat.objects.all(), "status", EmergencyChat.Status.choices),
        },
        "monthly": {
            "registrations": monthly(User.objects.all(), "date_joined"),
            "evaluations": monthly(evaluations, "created_at"),
            "appointments": monthly(appointments, "created_at"),
        },
    }
