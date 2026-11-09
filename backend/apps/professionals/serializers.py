import re

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.accounts.serializers import FIELD_ERRORS, RegisterSerializer, UserSerializer

from .models import PsychologistProfile, Specialty

LICENSE_REGEX = re.compile(r"^[A-Z0-9-]{4,30}$")


class ProfileFieldsMixin(serializers.Serializer):
    """Datos profesionales (CA1 a CA5 de OM3-21)."""

    specialty = serializers.ChoiceField(
        choices=Specialty.choices,
        error_messages={**FIELD_ERRORS, "invalid_choice": "Selecciona una especialidad válida."},
    )
    years_experience = serializers.IntegerField(
        min_value=0,
        max_value=60,
        error_messages={
            **FIELD_ERRORS,
            "invalid": "Ingresa un número de años válido.",
            "min_value": "Los años de experiencia no pueden ser negativos.",
            "max_value": "Ingresa un número de años válido (máximo 60).",
        },
    )
    experience = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    license_number = serializers.CharField(max_length=30, error_messages=FIELD_ERRORS)
    university = serializers.CharField(max_length=150, required=False, allow_blank=True)
    description = serializers.CharField(
        min_length=30,
        max_length=1000,
        error_messages={
            **FIELD_ERRORS,
            "min_length": "Cuéntale a los pacientes un poco más sobre ti (mínimo 30 caracteres).",
            "max_length": "La descripción no puede superar los 1000 caracteres.",
        },
    )

    def validate_license_number(self, value):
        value = value.strip().upper().replace(" ", "")
        if not LICENSE_REGEX.match(value):
            raise serializers.ValidationError(
                "La tarjeta profesional solo puede tener letras, números y guiones (4 a 30 caracteres)."
            )
        existing = PsychologistProfile.objects.filter(license_number=value)
        instance = getattr(self, "instance", None)
        if isinstance(instance, PsychologistProfile):
            existing = existing.exclude(pk=instance.pk)
        if existing.exists():
            raise serializers.ValidationError("Esta tarjeta profesional ya está registrada.")
        return value

    def validate_description(self, value):
        return value.strip()


PROFILE_FIELDS = ("specialty", "years_experience", "experience", "license_number", "university", "description")


class ProfessionalRegisterSerializer(ProfileFieldsMixin, RegisterSerializer):
    """Registro de psicólogo: datos de la cuenta + datos profesionales."""

    class Meta(RegisterSerializer.Meta):
        fields = RegisterSerializer.Meta.fields + PROFILE_FIELDS

    @transaction.atomic
    def create(self, validated_data):
        profile_data = {field: validated_data.pop(field) for field in PROFILE_FIELDS if field in validated_data}
        validated_data.pop("password_confirm")
        from apps.accounts.models import User

        user = User.objects.create_user(role=User.Role.PSICOLOGO, **validated_data)
        PsychologistProfile.objects.create(user=user, **profile_data)
        return user


class ProfileSerializer(ProfileFieldsMixin, serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    specialty_display = serializers.CharField(source="get_specialty_display", read_only=True)

    class Meta:
        model = PsychologistProfile
        fields = ("id", "user", *PROFILE_FIELDS, "specialty_display", "is_verified", "verified_at", "created_at")
        read_only_fields = ("is_verified", "verified_at", "created_at")


class VerifySerializer(serializers.Serializer):
    is_verified = serializers.BooleanField()

    def update(self, instance, validated_data):
        instance.is_verified = validated_data["is_verified"]
        instance.verified_at = timezone.now() if instance.is_verified else None
        instance.save(update_fields=["is_verified", "verified_at", "updated_at"])
        return instance


class DirectorySerializer(serializers.ModelSerializer):
    """Lo que un paciente ve de cada psicólogo verificado: foto, especialidad y mini descripción."""

    id = serializers.IntegerField(source="user.id", read_only=True)
    full_name = serializers.CharField(source="user.get_full_name", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    avatar_url = serializers.CharField(source="user.avatar_url", read_only=True, allow_null=True)
    specialty_display = serializers.CharField(source="get_specialty_display", read_only=True)
    next_available = serializers.SerializerMethodField()

    class Meta:
        model = PsychologistProfile
        fields = (
            "id", "full_name", "first_name", "avatar_url", "specialty", "specialty_display",
            "years_experience", "university", "description", "experience", "next_available",
        )
        read_only_fields = fields

    def get_next_available(self, obj) -> str | None:
        """Primer horario libre (para mostrar 'Próximo horario' en el listado)."""
        from apps.appointments.slots import available_slots, local_tz

        slots = available_slots(obj.user)
        return slots[0].astimezone(local_tz()).isoformat() if slots else None
