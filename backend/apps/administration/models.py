from django.conf import settings
from django.db import models


class AdminActionLog(models.Model):
    """OM3-24 CA4: cada acción administrativa queda registrada (quién, qué, a quién y cuándo)."""

    class Action(models.TextChoices):
        USER_ACTIVATED = "USER_ACTIVATED", "Activó una cuenta"
        USER_DEACTIVATED = "USER_DEACTIVATED", "Desactivó una cuenta"
        PROFESSIONAL_VERIFIED = "PROFESSIONAL_VERIFIED", "Verificó a un psicólogo"
        PROFESSIONAL_UNVERIFIED = "PROFESSIONAL_UNVERIFIED", "Retiró la verificación de un psicólogo"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="administrador", on_delete=models.SET_NULL, null=True,
        related_name="admin_actions",
    )
    action = models.CharField("acción", max_length=30, choices=Action.choices)
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="usuario afectado", on_delete=models.SET_NULL, null=True,
        related_name="admin_actions_received",
    )
    # se guarda el correo por si la cuenta afectada se elimina más adelante
    target_email = models.EmailField("correo del usuario afectado")
    reason = models.CharField("motivo", max_length=300, blank=True)
    created_at = models.DateTimeField("fecha", auto_now_add=True)

    class Meta:
        verbose_name = "acción administrativa"
        verbose_name_plural = "registro de acciones administrativas"
        ordering = ("-created_at",)

    def __str__(self):
        actor = self.actor.email if self.actor else "—"
        return f"{actor}: {self.get_action_display()} ({self.target_email})"


def log_action(actor, action, target, reason=""):
    return AdminActionLog.objects.create(
        actor=actor, action=action, target=target, target_email=target.email, reason=(reason or "").strip()
    )
