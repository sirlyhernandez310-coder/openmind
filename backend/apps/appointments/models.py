from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Weekday(models.IntegerChoices):
    LUNES = 0, "Lunes"
    MARTES = 1, "Martes"
    MIERCOLES = 2, "Miércoles"
    JUEVES = 3, "Jueves"
    VIERNES = 4, "Viernes"
    SABADO = 5, "Sábado"
    DOMINGO = 6, "Domingo"


class Availability(models.Model):
    """Franja semanal en la que el psicólogo atiende (ej. lunes de 8:00 a 12:00)."""

    psychologist = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="availabilities", verbose_name="psicólogo"
    )
    weekday = models.PositiveSmallIntegerField("día", choices=Weekday.choices)
    start_time = models.TimeField("desde")
    end_time = models.TimeField("hasta")

    class Meta:
        verbose_name = "horario de atención"
        verbose_name_plural = "horarios de atención"
        ordering = ("weekday", "start_time")

    def __str__(self):
        return f"{self.get_weekday_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}"

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("La hora de inicio debe ser anterior a la hora de fin.")


class Appointment(models.Model):
    class Status(models.TextChoices):
        PROGRAMADA = "PROGRAMADA", "Programada"
        CANCELADA = "CANCELADA", "Cancelada"
        REALIZADA = "REALIZADA", "Realizada"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="appointments", verbose_name="paciente"
    )
    psychologist = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sessions", verbose_name="psicólogo"
    )
    start = models.DateTimeField("inicio")
    end = models.DateTimeField("fin")
    reason = models.CharField("motivo de consulta", max_length=500, blank=True)
    status = models.CharField("estado", max_length=12, choices=Status.choices, default=Status.PROGRAMADA)
    created_at = models.DateTimeField("reservada el", auto_now_add=True)

    class Meta:
        verbose_name = "cita"
        verbose_name_plural = "citas"
        ordering = ("start",)
        constraints = [
            # La base de datos impide que dos pacientes reserven el mismo horario (CA5 de OM3-17)
            models.UniqueConstraint(
                fields=("psychologist", "start"),
                condition=Q(status="PROGRAMADA"),
                name="unique_active_slot_per_psychologist",
            ),
            models.UniqueConstraint(
                fields=("patient", "start"),
                condition=Q(status="PROGRAMADA"),
                name="unique_active_slot_per_patient",
            ),
        ]

    def __str__(self):
        return f"{self.patient.email} con {self.psychologist.email} · {self.start:%Y-%m-%d %H:%M}"
