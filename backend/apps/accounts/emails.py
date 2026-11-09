"""
Correos transaccionales de OpenMind: verificación de correo y recuperación de contraseña.
Ambos usan la misma configuración de envío (EMAIL_BACKEND en settings / .env).
"""
import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core import signing
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

logger = logging.getLogger(__name__)

VERIFY_SALT = "openmind.verify-email"


def _send(user, subject, template, context, dev_label):
    """Renderiza la plantilla (versión texto + HTML) y envía el correo."""
    context = {"user": user, **context}
    text_body = render_to_string(f"accounts/{template}.txt", context)
    html_body = render_to_string(f"accounts/{template}.html", context)
    message = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [user.email])
    message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=False)
    logger.info("Correo '%s' enviado a %s", subject, user.email)
    if settings.DEBUG and "console" in settings.EMAIL_BACKEND:
        # en desarrollo el correo sale codificado en la terminal; dejamos el enlace limpio para copiarlo
        logger.info("\n🔑 %s (desarrollo): %s\n", dev_label, context["link"])
    return context["link"]


# ------------------------------------------------------------ Verificación de correo
def make_verification_token(user):
    """Token firmado con la clave secreta: contiene el id y el correo, y vence según EMAIL_VERIFICATION_HOURS."""
    return signing.dumps({"uid": user.pk, "email": user.email}, salt=VERIFY_SALT, compress=True)


def read_verification_token(token):
    """Devuelve el dict del token o lanza signing.BadSignature / SignatureExpired."""
    return signing.loads(token, salt=VERIFY_SALT, max_age=settings.EMAIL_VERIFICATION_HOURS * 3600)


def send_verification_email(user):
    link = f"{settings.FRONTEND_URL}/verificar-correo?token={make_verification_token(user)}"
    return _send(
        user,
        "OpenMind · Confirma tu correo",
        "verify_email",
        {"link": link, "hours": settings.EMAIL_VERIFICATION_HOURS},
        "ENLACE DE VERIFICACIÓN",
    )


# --------------------------------------------------------- Recuperación de contraseña
def build_reset_link(user):
    """Arma el enlace que el usuario abre para crear su nueva contraseña."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return f"{settings.FRONTEND_URL}/restablecer-contrasena?uid={uid}&token={token}"


def send_password_reset_email(user):
    return _send(
        user,
        "OpenMind · Recupera tu contraseña",
        "password_reset_email",
        {"link": build_reset_link(user), "minutes": settings.PASSWORD_RESET_TIMEOUT // 60},
        "ENLACE DE RECUPERACIÓN",
    )
