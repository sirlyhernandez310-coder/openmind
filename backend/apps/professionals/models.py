from django.conf import settings
from django.core.validators import MaxValueValidator, MinLengthValidator
from django.db import models


class Specialty(models.TextChoices):
    CLINICA = "CLINICA", "Psicología clínica"
    SALUD = "SALUD", "Psicología de la salud"
    INFANTIL = "INFANTIL", "Psicología infantil y adolescente"
    EDUCATIVA = "EDUCATIVA", "Psicología educativa"
    ORGANIZACIONAL = "ORGANIZACIONAL", "Psicología organizacional"
    FAMILIA = "FAMILIA", "Terapia de pareja y familia"
    NEUROPSICOLOGIA = "NEUROPSICOLOGIA", "Neuropsicología"
    SOCIAL = "SOCIAL", "Psicología social y comunitaria"


class PsychologistProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="psychologist_profile", verbose_name="usuario"
    )
    specialty = models.CharField("especialidad", max_length=30, choices=Specialty.choices)
    years_experience = models.PositiveSmallIntegerField("años de experiencia", validators=[MaxValueValidator(60)])
    experience = models.TextField("experiencia", max_length=1000, blank=True,
                                  help_text="Lugares de trabajo, enfoques, poblaciones atendidas.")
    license_number = models.CharField("tarjeta profesional", max_length=30, unique=True)
    university = models.CharField("universidad", max_length=150, blank=True)
    description = models.TextField("descripción profesional", max_length=1000, validators=[MinLengthValidator(30)])
    is_verified = models.BooleanField("verificado", default=False)
    verified_at = models.DateTimeField("fecha de verificación", null=True, blank=True)
    created_at = models.DateTimeField("fecha de registro", auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "perfil profesional"
        verbose_name_plural = "perfiles profesionales"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.get_full_name()} · {self.get_specialty_display()} · TP {self.license_number}"
