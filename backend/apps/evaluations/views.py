from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import role_permission

from .models import SCALE, Evaluation, Question
from .serializers import (
    EvaluationCreateSerializer,
    EvaluationDetailSerializer,
    EvaluationListSerializer,
    QuestionSerializer,
)

User = get_user_model()

QuestionnaireSerializer = inline_serializer(
    "Cuestionario",
    {
        "instructions": serializers.CharField(),
        "scale": inline_serializer("Opcion", {"value": serializers.IntegerField(), "label": serializers.CharField()}, many=True),
        "questions": QuestionSerializer(many=True),
    },
)


@extend_schema_view(
    list=extend_schema(summary="Historial: mis evaluaciones anteriores"),
    retrieve=extend_schema(summary="Resultado de una evaluación"),
    create=extend_schema(
        summary="Enviar respuestas y obtener el resultado",
        request=EvaluationCreateSerializer,
        responses={201: EvaluationDetailSerializer},
    ),
)
@extend_schema(tags=["Evaluación emocional"])
class EvaluationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    permission_classes = (role_permission(User.Role.PACIENTE),)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # generación del esquema Swagger
            return Evaluation.objects.none()
        # Historial disponible únicamente para el usuario correspondiente (CA5 OM3-13)
        queryset = self.request.user.evaluations.all()
        if self.action == "retrieve":
            queryset = queryset.prefetch_related("answers__question")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return EvaluationListSerializer
        if self.action == "create":
            return EvaluationCreateSerializer
        return EvaluationDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        evaluation = serializer.save()
        detail = EvaluationDetailSerializer(evaluation, context=self.get_serializer_context())
        return Response(detail.data, status=status.HTTP_201_CREATED)

    @extend_schema(summary="Iniciar evaluación: preguntas y escala de respuesta", responses=QuestionnaireSerializer)
    @action(detail=False, methods=["get"])
    def questions(self, request):
        return Response(
            {
                "instructions": "Piensa en las últimas dos semanas. ¿Con qué frecuencia te has sentido así?",
                "scale": [{"value": value, "label": label} for value, label in SCALE],
                "questions": QuestionSerializer(Question.objects.filter(is_active=True), many=True).data,
            }
        )
