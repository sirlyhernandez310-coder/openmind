from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import generics, permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import role_permission
from apps.accounts.views import register_and_send_verification

from .models import PsychologistProfile, Specialty
from .serializers import DirectorySerializer, ProfessionalRegisterSerializer, ProfileSerializer, VerifySerializer

User = get_user_model()


@extend_schema(
    tags=["Registro profesional"],
    summary="Registrar un psicólogo con sus datos profesionales y enviar el correo de verificación",
    responses={201: inline_serializer("RegistroProfesionalPendiente", {
        "detail": serializers.CharField(), "email": serializers.EmailField()})},
)
class ProfessionalRegisterView(generics.CreateAPIView):
    serializer_class = ProfessionalRegisterSerializer
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return register_and_send_verification(serializer)


@extend_schema(tags=["Registro profesional"], summary="Lista de especialidades disponibles")
class SpecialtyListView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()

    @extend_schema(responses=inline_serializer("Especialidad", {
        "value": serializers.CharField(), "label": serializers.CharField()}, many=True))
    def get(self, request):
        return Response([{"value": value, "label": label} for value, label in Specialty.choices])


@extend_schema(tags=["Registro profesional"])
class MyProfileView(generics.RetrieveUpdateAPIView):
    """El psicólogo consulta y actualiza su perfil profesional."""

    serializer_class = ProfileSerializer
    permission_classes = (role_permission(User.Role.PSICOLOGO),)
    http_method_names = ("get", "patch")

    @extend_schema(summary="Mi perfil profesional")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Actualizar mi perfil profesional")
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def get_object(self):
        return generics.get_object_or_404(PsychologistProfile, user=self.request.user)


@extend_schema(
    tags=["Registro profesional"],
    summary="Listar profesionales (administrador)",
    parameters=[OpenApiParameter("verified", bool, description="Filtrar por verificados (true/false)")],
)
class ProfessionalListView(generics.ListAPIView):
    serializer_class = ProfileSerializer
    permission_classes = (role_permission(User.Role.ADMINISTRADOR),)

    def get_queryset(self):
        queryset = PsychologistProfile.objects.select_related("user")
        verified = self.request.query_params.get("verified")
        if verified in ("true", "false"):
            queryset = queryset.filter(is_verified=verified == "true")
        return queryset


@extend_schema(
    tags=["Registro profesional"],
    summary="Verificar o retirar la verificación de un profesional (administrador)",
    request=VerifySerializer,
    responses=ProfileSerializer,
)
class VerifyProfessionalView(APIView):
    permission_classes = (role_permission(User.Role.ADMINISTRADOR),)

    def post(self, request, pk):
        profile = generics.get_object_or_404(PsychologistProfile, pk=pk)
        serializer = VerifySerializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ProfileSerializer(profile).data)


@extend_schema(
    tags=["Registro profesional"],
    summary="Directorio de psicólogos verificados (foto, especialidad y mini descripción)",
    parameters=[
        OpenApiParameter("specialty", str, description="Filtrar por especialidad (ej. CLINICA)"),
        OpenApiParameter("q", str, description="Buscar por nombre, especialidad o descripción"),
    ],
)
class DirectoryListView(generics.ListAPIView):
    serializer_class = DirectorySerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = (
            PsychologistProfile.objects.filter(is_verified=True, user__is_active=True)
            .select_related("user")
            .defer("user__avatar")
            .order_by("user__first_name")
        )
        specialty = self.request.query_params.get("specialty")
        if specialty:
            queryset = queryset.filter(specialty=specialty.upper())
        search = (self.request.query_params.get("q") or "").strip()
        for word in search.split():
            matching_specialties = [value for value, label in Specialty.choices if word.lower() in label.lower()]
            queryset = queryset.filter(
                Q(user__first_name__icontains=word)
                | Q(user__last_name__icontains=word)
                | Q(description__icontains=word)
                | Q(specialty__in=matching_specialties)
            )
        return queryset


@extend_schema(tags=["Registro profesional"], summary="Perfil público de un psicólogo verificado")
class DirectoryDetailView(generics.RetrieveAPIView):
    serializer_class = DirectorySerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = "user_id"
    lookup_url_kwarg = "user_id"

    def get_queryset(self):
        return PsychologistProfile.objects.filter(is_verified=True, user__is_active=True).select_related("user")
