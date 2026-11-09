import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import Http404, HttpResponse
from django.views.decorators.cache import cache_control
from django.utils.decorators import method_decorator
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import generics, parsers, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .emails import send_password_reset_email, send_verification_email
from .permissions import role_permission
from .serializers import (
    AvatarSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PasswordResetTokenSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)

DetailSerializer = inline_serializer("Mensaje", {"detail": serializers.CharField()})
SessionSerializer = inline_serializer(
    "Sesion",
    {"access": serializers.CharField(), "refresh": serializers.CharField(), "user": UserSerializer()},
)
RegisteredSerializer = inline_serializer(
    "RegistroPendiente", {"detail": serializers.CharField(), "email": serializers.EmailField()}
)
EMAIL_FAILED_MSG = "No pudimos enviar el correo en este momento. Intenta de nuevo más tarde."


def session_for(user):
    refresh = LoginSerializer.get_token(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh), "user": UserSerializer(user).data}


def register_and_send_verification(serializer):
    """
    Crea la cuenta y envía el correo de verificación en una sola transacción:
    si el correo no se puede enviar, la cuenta no queda creada.
    """
    try:
        with transaction.atomic():
            user = serializer.save()
            send_verification_email(user)
    except Exception:
        logger.exception("Registro cancelado: no se pudo enviar el correo de verificación")
        return Response({"detail": EMAIL_FAILED_MSG}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    return Response(
        {
            "detail": f"Te enviamos un enlace a {user.email} para confirmar tu correo y activar tu cuenta.",
            "email": user.email,
        },
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    tags=["Autenticación"],
    summary="Registrar un nuevo usuario (paciente) y enviar el correo de verificación",
    responses={
        201: RegisteredSerializer,
        400: OpenApiResponse(description="Datos inválidos o correo ya registrado"),
        503: OpenApiResponse(DetailSerializer, description="No se pudo enviar el correo"),
    },
)
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return register_and_send_verification(serializer)


@extend_schema(
    tags=["Verificación de correo"],
    summary="Confirmar el correo con el enlace recibido (inicia sesión automáticamente)",
    request=VerifyEmailSerializer,
    responses={200: SessionSerializer, 400: OpenApiResponse(description="Enlace inválido o vencido")},
)
class VerifyEmailView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["token"]
        if not user.email_verified:
            user.email_verified = True
            user.save(update_fields=["email_verified"])
        # CA5 del registro: al completar el registro (confirmar el correo) entra a su cuenta
        return Response(session_for(user))


@extend_schema(
    tags=["Verificación de correo"],
    summary="Reenviar el correo de verificación",
    request=ResendVerificationSerializer,
    responses={200: DetailSerializer, 404: DetailSerializer, 503: DetailSerializer},
)
class ResendVerificationView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "verificacion"

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user is None:
            return Response(
                {"detail": "No encontramos una cuenta registrada con este correo."}, status=status.HTTP_404_NOT_FOUND
            )
        if user.email_verified:
            return Response({"detail": "Este correo ya está confirmado. Ya puedes iniciar sesión."})
        try:
            send_verification_email(user)
        except Exception:
            logger.exception("No se pudo reenviar la verificación a %s", email)
            return Response({"detail": EMAIL_FAILED_MSG}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({"detail": f"Te enviamos un nuevo enlace a {email}."})


@extend_schema(
    tags=["Autenticación"],
    summary="Iniciar sesión con correo y contraseña",
    responses={
        200: SessionSerializer,
        401: OpenApiResponse(DetailSerializer, description="Credenciales incorrectas"),
        403: OpenApiResponse(description="Correo sin confirmar (code: email_not_verified)"),
    },
)
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    authentication_classes = ()
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "login"


@extend_schema(tags=["Autenticación"], summary="Renovar el token de acceso con el refresh")
class RefreshView(TokenRefreshView):
    authentication_classes = ()


@extend_schema(
    tags=["Autenticación"],
    summary="Cerrar sesión (invalida el refresh token)",
    request=LogoutSerializer,
    responses={205: None, 400: DetailSerializer},
)
class LogoutView(APIView):
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError:
            return Response({"detail": "Token inválido o expirado."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_205_RESET_CONTENT)


@extend_schema(tags=["Autenticación"], summary="Datos del usuario autenticado")
class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


@extend_schema(tags=["Autenticación"], summary="Listar usuarios (solo administrador)")
class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = (role_permission(User.Role.ADMINISTRADOR),)

    def get_queryset(self):
        queryset = User.objects.all()
        role = self.request.query_params.get("role")
        if role:
            queryset = queryset.filter(role=role.upper())
        return queryset


@extend_schema(
    tags=["Recuperación de contraseña"],
    summary="Solicitar recuperación: envía las instrucciones al correo",
    request=PasswordResetRequestSerializer,
    responses={
        200: DetailSerializer,
        404: OpenApiResponse(DetailSerializer, description="El correo no está registrado"),
        503: OpenApiResponse(DetailSerializer, description="No se pudo enviar el correo"),
    },
)
class PasswordResetRequestView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "recuperacion"

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        # Criterio: el sistema debe verificar que el correo esté registrado
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user is None:
            return Response(
                {"detail": "No encontramos una cuenta registrada con este correo."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            send_password_reset_email(user)
        except Exception:  # error de SMTP, credenciales, red, etc.
            logger.exception("No se pudo enviar el correo de recuperación a %s", email)
            return Response({"detail": EMAIL_FAILED_MSG}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(
            {"detail": f"Te enviamos las instrucciones a {email}. Revisa tu bandeja de entrada (y la de spam)."}
        )


@extend_schema(
    tags=["Recuperación de contraseña"],
    summary="Verificar que el enlace de recuperación siga vigente",
    request=PasswordResetTokenSerializer,
    responses={200: DetailSerializer, 400: DetailSerializer},
)
class PasswordResetValidateView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()

    def post(self, request):
        serializer = PasswordResetTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"detail": "Enlace válido.", "email": serializer.validated_data["user"].email})


@extend_schema(
    tags=["Recuperación de contraseña"],
    summary="Establecer la nueva contraseña",
    request=PasswordResetConfirmSerializer,
    responses={200: DetailSerializer, 400: OpenApiResponse(description="Enlace inválido o contraseña no válida")},
)
class PasswordResetConfirmView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "¡Listo! Tu contraseña fue actualizada. Ya puedes iniciar sesión."})


@extend_schema(tags=["Foto de perfil"])
class MyAvatarView(APIView):
    """El usuario autenticado sube (PUT, multipart) o quita (DELETE) su foto de perfil."""

    parser_classes = (parsers.MultiPartParser, parsers.FormParser)

    @extend_schema(
        summary="Subir o cambiar mi foto de perfil (JPG, PNG o WEBP, máx. 5 MB)",
        request={"multipart/form-data": AvatarSerializer},
        responses={200: UserSerializer, 400: OpenApiResponse(description="Archivo inválido")},
    )
    def put(self, request):
        serializer = AvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_avatar(serializer.validated_data["avatar"])
        request.user.save(update_fields=["avatar", "avatar_key"])
        return Response(UserSerializer(request.user).data)

    @extend_schema(summary="Quitar mi foto de perfil", request=None, responses={200: UserSerializer})
    def delete(self, request):
        request.user.set_avatar(None)
        request.user.save(update_fields=["avatar", "avatar_key"])
        return Response(UserSerializer(request.user).data)


@method_decorator(cache_control(public=True, max_age=60 * 60 * 24 * 30, immutable=True), name="get")
@extend_schema(tags=["Foto de perfil"], summary="Ver una foto de perfil (imagen WebP)", responses={(200, "image/webp"): bytes})
class AvatarImageView(APIView):
    """La URL lleva una clave aleatoria que cambia con cada foto, así que no se puede adivinar."""

    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()

    def get(self, request, key):
        user = User.objects.filter(avatar_key=key).only("avatar").first()
        if user is None or not user.avatar:
            raise Http404
        return HttpResponse(bytes(user.avatar), content_type="image/webp")
