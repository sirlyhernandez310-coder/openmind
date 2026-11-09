"""Información clara sobre el servicio de atención (CA5 de OM3-19)."""
from django.conf import settings

DEFAULT_LINES = [
    {
        "name": "Línea 106 · Teleorientación en salud mental",
        "phone": "106",
        "detail": "Línea nacional del Ministerio de Salud, gratuita, 24 horas.",
    },
    {
        "name": "Línea Amiga Saludable (Medellín)",
        "phone": "6044444448",
        "display": "(604) 444 4448",
        "detail": "Atención psicológica 24 horas, todos los días.",
    },
    {
        "name": "Línea de emergencias",
        "phone": "123",
        "detail": "Si tu vida o la de otra persona está en peligro inmediato.",
    },
]


def service_info():
    return {
        "title": "Chat de emergencia OpenMind",
        "description": (
            "Un espacio para hablar con un psicólogo de OpenMind cuando necesites orientación inmediata. "
            "Al iniciar el chat te pondremos en una fila de atención y el primer profesional disponible "
            "se unirá a la conversación."
        ),
        "how_it_works": [
            "Inicia el chat y cuéntanos brevemente cómo te sientes.",
            "Un psicólogo verificado se unirá en cuanto esté disponible.",
            "Tu conversación es privada: solo la ven tú y el profesional que te atiende.",
            "Puedes finalizar el chat cuando quieras.",
        ],
        "hours": getattr(settings, "EMERGENCY_CHAT_HOURS", "Lunes a domingo, según disponibilidad de los profesionales."),
        "disclaimer": (
            "Este chat brinda orientación y primeros auxilios psicológicos; no reemplaza los servicios de urgencias. "
            "Si estás en peligro inmediato, llama al 123."
        ),
        "lines": getattr(settings, "EMERGENCY_LINES", DEFAULT_LINES),
    }
