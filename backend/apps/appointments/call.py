"""OM3-20 Videollamada: reglas de acceso y señalización WebRTC por consultas periódicas (polling)."""
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import Appointment


def call_window(appointment):
    """Desde cuándo y hasta cuándo se puede entrar a la videollamada de la cita."""
    opens = appointment.start - timedelta(minutes=settings.VIDEOCALL_EARLY_MINUTES)
    return opens, appointment.end


def join_problem(appointment, now=None):
    """Devuelve por qué no se puede entrar todavía, o None si se puede."""
    now = now or timezone.now()
    if appointment.status != Appointment.Status.PROGRAMADA:
        return "Esta sesión ya no está programada."
    opens, closes = call_window(appointment)
    if now < opens:
        return "La videollamada se habilita minutos antes de la hora de la sesión."
    if now > closes:
        return "Esta sesión ya terminó."
    return None


def ice_servers():
    servers = [{"urls": settings.VIDEOCALL_STUN_URLS}] if settings.VIDEOCALL_STUN_URLS else []
    if settings.VIDEOCALL_TURN_URLS:
        servers.append({
            "urls": settings.VIDEOCALL_TURN_URLS,
            "username": settings.VIDEOCALL_TURN_USERNAME,
            "credential": settings.VIDEOCALL_TURN_CREDENTIAL,
        })
    return servers
