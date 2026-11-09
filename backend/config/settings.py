"""
Configuración de Django para la API de OpenMind.

Todo lo sensible (claves, base de datos, correo) se lee de variables de
entorno o del archivo backend/.env (ver .env.example).
"""
import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-solo-desarrollo-cambiar")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceros
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    # Apps propias
    "apps.accounts",
    "apps.evaluations",
    "apps.professionals",
    "apps.emergency",
    "apps.appointments",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

AUTH_USER_MODEL = "accounts.User"


# Base de datos: SQLite en local; en producción basta con definir DATABASE_URL
# (por ejemplo la URL de PostgreSQL que entrega Render o Railway).
# (si DATABASE_URL está vacía o no existe, se usa SQLite)
DATABASES = {
    "default": dj_database_url.parse(
        os.getenv("DATABASE_URL") or f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}


# Contraseñas: Django las guarda encriptadas (PBKDF2 + SHA256 con sal).
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# CORS: dominios del frontend que pueden llamar a la API
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")

# URL del frontend: se usa para armar el enlace de recuperación de contraseña
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")


# Correo electrónico
# En desarrollo los correos se imprimen en la terminal (console backend).
# En producción se configura SMTP (Gmail, Brevo, etc.) con variables de entorno.
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "OpenMind <no-responder@openmind.app>")
EMAIL_TIMEOUT = 15

# Brevo (envío por API HTTP, útil en Render donde el SMTP está bloqueado)
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")

# Citas (Sprint 3)
APPOINTMENT_MINUTES = int(os.getenv("APPOINTMENT_MINUTES", "60"))  # duración de cada sesión
APPOINTMENT_DAYS_AHEAD = int(os.getenv("APPOINTMENT_DAYS_AHEAD", "14"))  # cuántos días hacia adelante se puede reservar
APPOINTMENT_MIN_NOTICE_MINUTES = int(os.getenv("APPOINTMENT_MIN_NOTICE_MINUTES", "60"))  # anticipación mínima

# El enlace para verificar el correo vence en 24 horas
EMAIL_VERIFICATION_HOURS = int(os.getenv("EMAIL_VERIFICATION_HOURS", "24"))

# El enlace para restablecer la contraseña vence en 1 hora
PASSWORD_RESET_TIMEOUT = int(os.getenv("PASSWORD_RESET_TIMEOUT", "3600"))


# DRF y JWT
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Límite de intentos para frenar ataques de fuerza bruta
    "DEFAULT_THROTTLE_RATES": {
        "login": os.getenv("THROTTLE_LOGIN", "10/min"),
        "recuperacion": os.getenv("THROTTLE_RECUPERACION", "5/min"),
        "verificacion": os.getenv("THROTTLE_VERIFICACION", "5/min"),
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "30"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "1"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "OpenMind API",
    "DESCRIPTION": (
        "API REST de **OpenMind**, plataforma de psicología y gestión emocional.\n\n"
        "**Sprint 1 · Gestión de usuarios:** registro, inicio de sesión con roles "
        "(paciente, psicólogo, administrador) y recuperación de contraseña.\n\n"
        "**Sprint 2 · Bienestar emocional:** evaluación emocional, historial, registro profesional "
        "de psicólogos y chat de emergencia.\n\n"
        "**Sprint 3 · Citas:** búsqueda de psicólogos, perfil, horarios disponibles, reserva y mis sesiones.\n\n"
        "Para probar endpoints protegidos: haz login, copia el `access` y pulsa **Authorize** "
        "(se envía como `Bearer <token>`)."
    ),
    "VERSION": "3.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "docExpansion": "list",
        "filter": True,
    },
    "TAGS": [
        {"name": "Autenticación", "description": "Registro, login, tokens y perfil"},
        {"name": "Verificación de correo", "description": "Confirmar que el correo existe y es del usuario"},
        {"name": "Recuperación de contraseña", "description": "Solicitud y restablecimiento"},
        {"name": "Foto de perfil", "description": "Subir, quitar y ver fotos de pacientes y psicólogos"},
        {"name": "Evaluación emocional", "description": "Cuestionario, resultado e historial (paciente)"},
        {"name": "Registro profesional", "description": "Registro y perfil de psicólogos, verificación"},
        {"name": "Citas", "description": "Horarios disponibles, reservas y mis sesiones"},
        {"name": "Chat de emergencia", "description": "Fila de atención y mensajes paciente ↔ psicólogo"},
    ],
}

# Seguridad extra en producción
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"apps": {"handlers": ["console"], "level": "INFO"}},
}
