from datetime import date

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view, inline_serializer
from rest_framework import generics, mixins, permissions, serializers, status, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import role_permission

from .models import Appointment, Availability
from .serializers import (
    AppointmentCreateSerializer,
    AppointmentSerializer,
    AvailabilityListSerializer,
    AvailabilitySerializer,
)
from .slots import available_slots, group_by_day

User = get_user_model()

SlotsSerializer = inline_serializer(
    "HorariosDisponibles",
    {
        "psychologist": serializers.IntegerField(),
        "session_minutes": serializers.IntegerField(),
        "days": inline_serializer(
            "DiaDisponible",
            {
                "date": serializers.DateField(),
                "slots": inline_serializer(
                    "Espacio", {"start": serializers.DateTimeField(), "end": serializers.DateTimeField()}, many=True
                ),
            },
            many=True,
        ),
    },
)


@extend_schema(
    tags=["Citas"],
    summary="Horarios disponibles de un psicólogo (solo los libres)",
    parameters=[
        OpenApiParameter("from", str, description="Fecha inicial AAAA-MM-DD (por defecto hoy)"),
        OpenApiParameter("days", int, description="Cuántos días mostrar (máx. según configuración)"),
    ],
    responses=SlotsSerializer,
)
class AvailableSlotsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, psychologist_id):
        from django.conf import settings

        psychologist = User.objects.filter(
            pk=psychologist_id, role=User.Role.PSICOLOGO, is_active=True, psychologist_profile__is_verified=True
        ).first()
        if psychologist is None:
            raise NotFound("El psicólogo no existe o no está disponible.")
        start_date = None
        if request.query_params.get("from"):
            try:
                start_date = date.fromisoformat(request.query_params["from"])
            except ValueError:
                raise ValidationError({"from": "Usa el formato AAAA-MM-DD."})
        days = request.query_params.get("days")
        days = min(int(days), settings.APPOINTMENT_DAYS_AHEAD) if days and days.isdigit() and int(days) > 0 else None
        slots = available_slots(psychologist, start_date, days)
        return Response(
            {"psychologist": psychologist.pk, "session_minutes": settings.APPOINTMENT_MINUTES, "days": group_by_day(slots)}
        )


@extend_schema_view(
    list=extend_schema(
        summary="Mis sesiones (paciente) o mi agenda (psicólogo)",
        parameters=[OpenApiParameter("scope", str, enum=["upcoming", "past", "all"], description="Por defecto upcoming")],
    ),
    retrieve=extend_schema(summary="Detalle de una cita"),
    create=extend_schema(
        summary="Reservar una cita (paciente)", request=AppointmentCreateSerializer, responses={201: AppointmentSerializer}
    ),
)
@extend_schema(tags=["Citas"])
class AppointmentViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    serializer_class = AppointmentSerializer

    def get_permissions(self):
        if self.action == "create":
            return [role_permission(User.Role.PACIENTE)()]
        return [role_permission(User.Role.PACIENTE, User.Role.PSICOLOGO)()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Appointment.objects.none()
        user = self.request.user
        queryset = Appointment.objects.select_related(
            "patient", "psychologist", "psychologist__psychologist_profile"
        ).defer("patient__avatar", "psychologist__avatar")
        # cada quien solo ve sus propias citas
        queryset = queryset.filter(patient=user) if user.role == User.Role.PACIENTE else queryset.filter(psychologist=user)
        if self.action == "list":
            scope = self.request.query_params.get("scope", "upcoming")
            now = timezone.now()
            if scope == "upcoming":
                queryset = queryset.filter(end__gte=now, status=Appointment.Status.PROGRAMADA)
            elif scope == "past":
                queryset = queryset.filter(Q(end__lt=now) | ~Q(status=Appointment.Status.PROGRAMADA)).order_by("-start")
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = AppointmentCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()
        return Response(AppointmentSerializer(appointment).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Citas"])
class MyAvailabilityView(APIView):
    """El psicólogo consulta y define su horario semanal de atención."""

    permission_classes = (role_permission(User.Role.PSICOLOGO),)

    @extend_schema(summary="Mi horario semanal (psicólogo)", responses=AvailabilitySerializer(many=True))
    def get(self, request):
        return Response(AvailabilitySerializer(request.user.availabilities.all(), many=True).data)

    @extend_schema(
        summary="Guardar mi horario semanal (reemplaza el anterior)",
        request=AvailabilityListSerializer,
        responses=AvailabilitySerializer(many=True),
    )
    def put(self, request):
        serializer = AvailabilityListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            request.user.availabilities.all().delete()
            Availability.objects.bulk_create(
                Availability(psychologist=request.user, **item) for item in serializer.validated_data["items"]
            )
        return Response(AvailabilitySerializer(request.user.availabilities.all(), many=True).data)
