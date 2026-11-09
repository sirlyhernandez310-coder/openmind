from django.conf import settings
from django.db import models


class EmergencyChat(models.Model):
    class Status(models.TextChoices):
        ESPERANDO = "ESPERANDO", "Esperando psicólogo"
        ACTIVA = "ACTIVA", "En atención"
        CERRADA = "CERRADA", "Finalizada"

    OPEN_STATUSES = (Status.ESPERANDO, Status.ACTIVA)

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="emergency_chats", verbose_name="paciente"
    )
    psychologist = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="attended_chats", verbose_name="psicólogo",
    )
    status = models.CharField("estado", max_length=12, choices=Status.choices, default=Status.ESPERANDO)
    created_at = models.DateTimeField("solicitado", auto_now_add=True)
    taken_at = models.DateTimeField("atendido", null=True, blank=True)
    closed_at = models.DateTimeField("finalizado", null=True, blank=True)

    class Meta:
        verbose_name = "chat de emergencia"
        verbose_name_plural = "chats de emergencia"
        ordering = ("-created_at",)

    def __str__(self):
        return f"Chat #{self.pk} · {self.patient.email} · {self.get_status_display()}"

    @property
    def is_open(self):
        return self.status in self.OPEN_STATUSES

    def is_participant(self, user):
        return user.pk in (self.patient_id, self.psychologist_id)


class Message(models.Model):
    chat = models.ForeignKey(EmergencyChat, on_delete=models.CASCADE, related_name="messages")
    # sender vacío = mensaje automático del sistema
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    text = models.TextField("mensaje", max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "mensaje"
        verbose_name_plural = "mensajes"
        ordering = ("created_at", "id")

    def __str__(self):
        return f"{self.sender or 'Sistema'}: {self.text[:40]}"
