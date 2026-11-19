from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import role_permission

from .models import AdminActionLog, log_action
from .serializers import ActionLogSerializer, AdminUserSerializer, UserStatusSerializer
from .stats import platform_stats

User = get_user_model()
IsAdmin = role_permission(User.Role.ADMINISTRADOR)


@extend_schema(
    tags=["Administración"],
    summary="Usuarios registrados (OM3-24)",
    parameters=[
        OpenApiParameter("q", str, description="Buscar por nombre o correo"),
        OpenApiParameter("role", str, description="PACIENTE, PSICOLOGO o ADMINISTRADOR"),
        OpenApiParameter("status", str, description="active o inactive"),
    ],
)
class AdminUserListView(generics.ListAPIView):
    serializer_class = AdminUserSerializer
    permission_classes = (IsAdmin,)

    def get_queryset(self):
        queryset = User.objects.select_related("psychologist_profile").order_by("-date_joined")
        params = self.request.query_params
        if params.get("role"):
            queryset = queryset.filter(role=params["role"].upper())
        if params.get("status") in ("active", "inactive"):
            queryset = queryset.filter(is_active=params["status"] == "active")
        for word in params.get("q", "").split():
            queryset = queryset.filter(
                Q(first_name__icontains=word) | Q(last_name__icontains=word) | Q(email__icontains=word)
            )
        return queryset


@extend_schema(tags=["Administración"], summary="Detalle de un usuario")
class AdminUserDetailView(generics.RetrieveAPIView):
    serializer_class = AdminUserSerializer
    permission_classes = (IsAdmin,)
    queryset = User.objects.select_related("psychologist_profile")


@extend_schema(
    tags=["Administración"],
    summary="Activar o desactivar una cuenta (queda en el registro de acciones)",
    request=UserStatusSerializer,
    responses={200: AdminUserSerializer, 400: OpenApiResponse(description="Acción no permitida")},
)
class AdminUserStatusView(APIView):
    permission_classes = (IsAdmin,)

    def post(self, request, pk):
        user = generics.get_object_or_404(User, pk=pk)
        serializer = UserStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_active = serializer.validated_data["is_active"]
        reason = serializer.validated_data.get("reason", "")

        # permisos establecidos: solo se gestionan cuentas de pacientes y psicólogos
        if user == request.user:
            return Response({"detail": "No puedes cambiar el estado de tu propia cuenta."}, status=status.HTTP_400_BAD_REQUEST)
        if user.role == User.Role.ADMINISTRADOR:
            return Response(
                {"detail": "Las cuentas de administrador no se gestionan desde aquí."}, status=status.HTTP_400_BAD_REQUEST
            )
        if not is_active and not reason.strip():
            return Response({"reason": ["Escribe el motivo para desactivar la cuenta."]}, status=status.HTTP_400_BAD_REQUEST)

        if user.is_active != is_active:
            user.is_active = is_active
            user.save(update_fields=["is_active"])
            action = AdminActionLog.Action.USER_ACTIVATED if is_active else AdminActionLog.Action.USER_DEACTIVATED
            log_action(request.user, action, user, reason)
        return Response(AdminUserSerializer(user).data)


@extend_schema(
    tags=["Administración"],
    summary="Registro de acciones administrativas",
    parameters=[OpenApiParameter("user", int, description="Solo las acciones sobre este usuario")],
)
class ActionLogListView(generics.ListAPIView):
    serializer_class = ActionLogSerializer
    permission_classes = (IsAdmin,)

    def get_queryset(self):
        queryset = AdminActionLog.objects.select_related("actor")
        if self.request.query_params.get("user", "").isdigit():
            queryset = queryset.filter(target_id=self.request.query_params["user"])
        return queryset[:200]


@extend_schema(
    tags=["Estadísticas"],
    summary="Estadísticas generales de la plataforma (OM3-25, solo administrador)",
    responses=inline_serializer("Estadisticas", {"generated_at": serializers.DateTimeField(), "users": serializers.DictField()}),
)
class StatsView(APIView):
    permission_classes = (IsAdmin,)

    def get(self, request):
        return Response(platform_stats())
