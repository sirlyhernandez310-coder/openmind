"""
Envío de correos por la API HTTP de Brevo (https://www.brevo.com).

Sirve cuando el hosting bloquea SMTP (por ejemplo el plan gratis de Render,
que bloquea los puertos 25, 465 y 587). Plan gratis de Brevo: 300 correos al día.

Uso en .env:
    EMAIL_BACKEND=apps.accounts.email_backends.BrevoEmailBackend
    BREVO_API_KEY=xkeysib-...
    DEFAULT_FROM_EMAIL=OpenMind <tu-correo-verificado-en-brevo@gmail.com>
"""
import json
import logging
import urllib.request
from email.utils import parseaddr

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)

BREVO_URL = "https://api.brevo.com/v3/smtp/email"


class BrevoEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, "BREVO_API_KEY", "")
        if not self.api_key and not fail_silently:
            raise ImproperlyConfigured("Falta BREVO_API_KEY en las variables de entorno.")

    def build_payload(self, message):
        name, address = parseaddr(message.from_email)
        payload = {
            "sender": {"email": address, **({"name": name} if name else {})},
            "to": [{"email": parseaddr(to)[1]} for to in message.to],
            "subject": message.subject,
            "textContent": message.body,
        }
        html = next((content for content, mime in getattr(message, "alternatives", []) if mime == "text/html"), None)
        if html:
            payload["htmlContent"] = html
        return payload

    def send_messages(self, email_messages):
        sent = 0
        for message in email_messages:
            request = urllib.request.Request(
                BREVO_URL,
                data=json.dumps(self.build_payload(message)).encode("utf-8"),
                headers={"api-key": self.api_key, "Content-Type": "application/json", "Accept": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=settings.EMAIL_TIMEOUT):
                    sent += 1
            except Exception:
                logger.exception("Brevo no pudo enviar el correo a %s", message.to)
                if not self.fail_silently:
                    raise
        return sent
