import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    """Usuario de OpenMind. Inicia sesión con su correo y tiene un rol."""

    class Role(models.TextChoices):
        PACIENTE = "PACIENTE", "Paciente"
        PSICOLOGO = "PSICOLOGO", "Psicólogo"
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"

    username = None
    email = models.EmailField("correo electrónico", unique=True)
    first_name = models.CharField("nombres", max_length=150)
    last_name = models.CharField("apellidos", max_length=150)
    phone = models.CharField("teléfono", max_length=20, blank=True)
    birth_date = models.DateField("fecha de nacimiento", null=True, blank=True)
    role = models.CharField("rol", max_length=20, choices=Role.choices, default=Role.PACIENTE)
    # se vuelve True cuando el usuario abre el enlace de verificación (o restablece su contraseña)
    email_verified = models.BooleanField("correo verificado", default=False)
    # Foto de perfil: se guarda ya recortada y comprimida (WebP 400x400) dentro de la base de datos,
    # así no se pierde en hostings con disco temporal como Render. Se sirve con una URL no adivinable.
    avatar = models.BinaryField("foto de perfil", null=True, blank=True, editable=False)
    avatar_key = models.UUIDField("clave de la foto", null=True, blank=True, editable=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ("-date_joined",)

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}> ({self.role})"

    @property
    def avatar_url(self):
        return f"/api/auth/avatars/{self.avatar_key}/" if self.avatar_key else None

    def set_avatar(self, data):
        self.avatar = data
        self.avatar_key = uuid.uuid4() if data else None
