from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.core import signing
from rest_framework import exceptions, serializers, status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

REQUIRED_MSG = "Este campo es obligatorio."
FIELD_ERRORS = {"required": REQUIRED_MSG, "blank": REQUIRED_MSG, "null": REQUIRED_MSG}
EMAIL_ERRORS = {**FIELD_ERRORS, "invalid": "Ingresa un correo electrónico válido (ej: nombre@correo.com)."}
INVALID_LINK_MSG = "El enlace de recuperación no es válido o ya expiró. Solicita uno nuevo."
UNVERIFIED_MSG = "Debes confirmar tu correo antes de iniciar sesión. Revisa tu bandeja de entrada."


class EmailNotVerified(exceptions.APIException):
    """403 con un código que el frontend usa para ofrecer reenviar el correo de verificación."""

    status_code = status.HTTP_403_FORBIDDEN

    def __init__(self, email):
        super().__init__({"detail": UNVERIFIED_MSG, "code": "email_not_verified", "email": email})


def check_passwords(attrs, user, field="password", confirm_field="password_confirm"):
    """Valida que las contraseñas coincidan y que cumplan las reglas de seguridad."""
    if attrs[field] != attrs[confirm_field]:
        raise serializers.ValidationError({confirm_field: "Las contraseñas no coinciden."})
    try:
        validate_password(attrs[field], user=user)
    except Exception as exc:  # django.core.exceptions.ValidationError
        raise serializers.ValidationError({field: list(getattr(exc, "messages", [str(exc)]))})


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    is_verified = serializers.SerializerMethodField()
    avatar_url = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = (
            "id", "email", "first_name", "last_name", "full_name",
            "phone", "birth_date", "role", "role_display", "is_verified", "email_verified",
            "avatar_url", "date_joined",
        )
        read_only_fields = fields

    def get_is_verified(self, obj) -> bool | None:
        """Solo aplica a psicólogos: indica si el administrador ya verificó su tarjeta profesional."""
        if obj.role != User.Role.PSICOLOGO:
            return None
        profile = getattr(obj, "psychologist_profile", None)
        return bool(profile and profile.is_verified)


# ---------------------------------------------------------------- Registro (OM3-9)
class RegisterSerializer(serializers.ModelSerializer):
    """
    CA1: datos requeridos · CA2: obligatorios completos · CA3: formato de correo
    CA4: correo ya registrado. El registro público siempre crea PACIENTES;
    los psicólogos tienen su propio registro profesional (Sprint 2) y el
    administrador se crea con `createsuperuser`.
    """

    email = serializers.EmailField(error_messages=EMAIL_ERRORS)
    first_name = serializers.CharField(max_length=150, error_messages=FIELD_ERRORS)
    last_name = serializers.CharField(max_length=150, error_messages=FIELD_ERRORS)
    phone = serializers.RegexField(
        r"^\+?[\d\s-]{7,20}$", required=False, allow_blank=True,
        error_messages={"invalid": "Ingresa un teléfono válido (solo números, 7 a 20 dígitos)."},
    )
    birth_date = serializers.DateField(required=False, allow_null=True)
    password = serializers.CharField(write_only=True, style={"input_type": "password"}, error_messages=FIELD_ERRORS)
    password_confirm = serializers.CharField(
        write_only=True, style={"input_type": "password"}, error_messages=FIELD_ERRORS
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "phone", "birth_date", "password", "password_confirm")

    def validate_email(self, value):
        value = value.strip().lower()
        existing = User.objects.filter(email__iexact=value).first()
        if existing and not existing.email_verified:
            raise serializers.ValidationError(
                "Este correo ya se registró pero aún no ha sido confirmado. Revisa tu correo o pide un nuevo enlace."
            )
        if existing:
            raise serializers.ValidationError("Este correo ya se encuentra registrado. ¿Quieres iniciar sesión?")
        return value

    def validate_first_name(self, value):
        return value.strip()

    def validate_last_name(self, value):
        return value.strip()

    def validate(self, attrs):
        candidate = User(email=attrs["email"], first_name=attrs["first_name"], last_name=attrs["last_name"])
        check_passwords(attrs, candidate)
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        return User.objects.create_user(role=User.Role.PACIENTE, **validated_data)


# ---------------------------------------------------------- Inicio de sesión (OM3-10)
class LoginSerializer(TokenObtainPairSerializer):
    """Valida credenciales y devuelve tokens JWT + datos del usuario con su rol."""

    default_error_messages = {
        "no_active_account": "Correo o contraseña incorrectos.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.username_field].error_messages.update(FIELD_ERRORS)
        self.fields["password"].error_messages.update(FIELD_ERRORS)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # el rol viaja dentro del token para que el frontend sepa qué interfaz mostrar
        token["role"] = user.role
        token["email"] = user.email
        token["full_name"] = user.get_full_name()
        return token

    def validate(self, attrs):
        attrs[self.username_field] = attrs[self.username_field].strip().lower()
        data = super().validate(attrs)
        # el correo debe estar confirmado para poder entrar
        if not self.user.email_verified:
            raise EmailNotVerified(self.user.email)
        data["user"] = UserSerializer(self.user).data
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(error_messages=FIELD_ERRORS)


# --------------------------------------------------- Recuperar contraseña (OM3-11)
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(error_messages=EMAIL_ERRORS)

    def validate_email(self, value):
        return value.strip().lower()


class PasswordResetTokenSerializer(serializers.Serializer):
    """Recibe uid + token del enlace enviado por correo y encuentra al usuario."""

    uid = serializers.CharField(error_messages=FIELD_ERRORS)
    token = serializers.CharField(error_messages=FIELD_ERRORS)

    def get_user(self, uid, token):
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(uid)), is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user is None or not default_token_generator.check_token(user, token):
            raise serializers.ValidationError({"detail": INVALID_LINK_MSG})
        return user

    def validate(self, attrs):
        attrs["user"] = self.get_user(attrs["uid"], attrs["token"])
        return attrs


class PasswordResetConfirmSerializer(PasswordResetTokenSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"}, error_messages=FIELD_ERRORS)
    password_confirm = serializers.CharField(
        write_only=True, style={"input_type": "password"}, error_messages=FIELD_ERRORS
    )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        check_passwords(attrs, attrs["user"])
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["password"])
        # abrir el enlace que llegó al correo también demuestra que el correo es suyo
        user.email_verified = True
        user.save(update_fields=["password", "email_verified"])
        # al cambiar la contraseña el token queda invalidado automáticamente
        return user


# ------------------------------------------------------------- Verificación de correo
class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField(error_messages=FIELD_ERRORS)

    def validate_token(self, value):
        from .emails import read_verification_token

        try:
            data = read_verification_token(value)
        except signing.SignatureExpired:
            raise serializers.ValidationError("El enlace de verificación expiró. Solicita uno nuevo.")
        except signing.BadSignature:
            raise serializers.ValidationError("El enlace de verificación no es válido.")
        user = User.objects.filter(pk=data.get("uid"), email__iexact=data.get("email"), is_active=True).first()
        if user is None:
            raise serializers.ValidationError("El enlace de verificación no es válido.")
        return user


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(error_messages=EMAIL_ERRORS)

    def validate_email(self, value):
        return value.strip().lower()


class AvatarSerializer(serializers.Serializer):
    avatar = serializers.ImageField(
        error_messages={
            "required": "Selecciona una foto.",
            "invalid": "Selecciona una foto válida.",
            "invalid_image": "El archivo no es una imagen válida.",
            "empty": "El archivo está vacío.",
        }
    )

    def validate_avatar(self, value):
        from .avatars import process_avatar

        return process_avatar(value)
