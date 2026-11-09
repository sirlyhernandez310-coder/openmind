from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view, inline_serializer
from rest_framework import mixins, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import EmergencyChat, Message
from .serializers import ChatSerializer, MessageCreateSerializer, MessageSerializer
from .service_info import service_info

User = get_user_model()

WELCOME = (
    "Hola {name}, recibimos tu solicitud. Un psicólogo de Open Mind se unirá a la conversación en cuanto esté "
    "disponible. Mientras tanto, puedes contarnos cómo te sientes. Si estás en peligro inmediato, llama al 123 "
    "o a la Línea 106."
)


class IsPatientOrVerifiedPsychologist(permissions.BasePermission):
    message = "El chat de emergencia está disponible para pacientes y psicólogos verificados."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.role == User.Role.PACIENTE:
            return True
        if user.role == User.Role.PSICOLOGO:
            profile = getattr(user, "psychologist_profile", None)
            if profile and profile.is_verified:
                return True
            self.message = "Tu perfil profesional debe estar verificado por un administrador para atender emergencias."
        return False


@extend_schema(
    tags=["Chat de emergencia"],
    summary="Información del servicio de atención",
    responses=inline_serializer("InfoServicio", {
        "title": serializers.CharField(), "description": serializers.CharField(),
        "how_it_works": serializers.ListField(child=serializers.CharField()),
        "hours": serializers.CharField(), "disclaimer": serializers.CharField(),
        "lines": serializers.ListField(child=serializers.DictField()),
    }),
)
class ServiceInfoView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()

    def get(self, request):
        return Response(service_info())


@extend_schema_view(
    list=extend_schema(
        summary="Mis chats (paciente) o fila de atención + mis chats (psicólogo)",
        parameters=[OpenApiParameter("status", str, enum=["ESPERANDO", "ACTIVA", "CERRADA"])],
    ),
    retrieve=extend_schema(summary="Detalle de un chat"),
    create=extend_schema(summary="Iniciar chat de emergencia (paciente)", request=None),
)
@extend_schema(tags=["Chat de emergencia"])
class EmergencyChatViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    serializer_class = ChatSerializer
    permission_classes = (IsPatientOrVerifiedPsychologist,)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # generación del esquema Swagger
            return EmergencyChat.objects.none()
        user = self.request.user
        queryset = EmergencyChat.objects.select_related(
            "patient", "psychologist", "psychologist__psychologist_profile"
        )
        if user.role == User.Role.PACIENTE:
            # la conversación está asociada solo a su paciente (CA4)
            queryset = queryset.filter(patient=user)
        else:
            queryset = queryset.filter(Q(status=EmergencyChat.Status.ESPERANDO) | Q(psychologist=user))
        status_filter = self.request.query_params.get("status")
        if status_filter and self.action == "list":
            queryset = queryset.filter(status=status_filter.upper())
        return queryset

    def create(self, request, *args, **kwargs):
        user = request.user
        if user.role != User.Role.PACIENTE:
            raise PermissionDenied("Solo los pacientes pueden iniciar un chat de emergencia.")
        # si ya tiene un chat abierto, se retoma en lugar de crear otro
        chat = EmergencyChat.objects.filter(patient=user, status__in=EmergencyChat.OPEN_STATUSES).first()
        created = chat is None
        if created:
            with transaction.atomic():
                chat = EmergencyChat.objects.create(patient=user)
                Message.objects.create(chat=chat, text=WELCOME.format(name=user.first_name))
        data = ChatSerializer(chat, context=self.get_serializer_context()).data
        return Response(data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @extend_schema(summary="Tomar un chat en espera (psicólogo verificado)", request=None)
    @action(detail=True, methods=["post"])
    def take(self, request, pk=None):
        if request.user.role != User.Role.PSICOLOGO:
            raise PermissionDenied("Solo los psicólogos pueden atender chats.")
        with transaction.atomic():
            chat = EmergencyChat.objects.select_for_update().get(pk=self.get_object().pk)
            if chat.status != EmergencyChat.Status.ESPERANDO:
                raise ValidationError({"detail": "Este chat ya fue tomado por otro profesional o fue cerrado."})
            chat.psychologist = request.user
            chat.status = EmergencyChat.Status.ACTIVA
            chat.taken_at = timezone.now()
            chat.save(update_fields=["psychologist", "status", "taken_at"])
            Message.objects.create(
                chat=chat, text=f"{request.user.get_full_name()} (psicólogo) se unió a la conversación."
            )
        return Response(ChatSerializer(chat, context=self.get_serializer_context()).data)

    @extend_schema(summary="Finalizar el chat", request=None)
    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        chat = self.get_object()
        if not chat.is_participant(request.user):
            raise PermissionDenied("Solo los participantes pueden finalizar el chat.")
        if chat.is_open:
            chat.status = EmergencyChat.Status.CERRADA
            chat.closed_at = timezone.now()
            chat.save(update_fields=["status", "closed_at"])
            Message.objects.create(chat=chat, text=f"{request.user.get_full_name()} finalizó la conversación.")
        return Response(ChatSerializer(chat, context=self.get_serializer_context()).data)

    @extend_schema(
        methods=["get"],
        summary="Mensajes del chat (usa ?after=<id> para traer solo los nuevos)",
        parameters=[OpenApiParameter("after", int)],
        responses=MessageSerializer(many=True),
    )
    @extend_schema(methods=["post"], summary="Enviar un mensaje", request=MessageCreateSerializer,
                   responses={201: MessageSerializer})
    @action(detail=True, methods=["get", "post"])
    def messages(self, request, pk=None):
        chat = self.get_object()
        if request.method == "GET":
            queryset = chat.messages.select_related("sender")
            after = request.query_params.get("after")
            if after and after.isdigit():
                queryset = queryset.filter(id__gt=int(after))
            return Response(MessageSerializer(queryset, many=True, context={"request": request}).data)

        if not chat.is_participant(request.user):
            raise PermissionDenied("Debes tomar el chat antes de escribir.")
        if not chat.is_open:
            raise ValidationError({"detail": "Esta conversación ya finalizó. Puedes iniciar un nuevo chat."})
        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = Message.objects.create(chat=chat, sender=request.user, text=serializer.validated_data["text"])
        return Response(MessageSerializer(message, context={"request": request}).data, status=status.HTTP_201_CREATED)
