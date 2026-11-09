from django.db import transaction
from rest_framework import serializers

from .models import MAX_VALUE, SCALE, Answer, Evaluation, Question
from .scoring import interpretation, score_answers


class QuestionSerializer(serializers.ModelSerializer):
    dimension_display = serializers.CharField(source="get_dimension_display", read_only=True)

    class Meta:
        model = Question
        fields = ("id", "order", "text", "dimension", "dimension_display")


class AnswerInputSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    value = serializers.IntegerField(
        min_value=0,
        max_value=MAX_VALUE,
        error_messages={
            "min_value": f"La respuesta debe estar entre 0 y {MAX_VALUE}.",
            "max_value": f"La respuesta debe estar entre 0 y {MAX_VALUE}.",
            "invalid": "La respuesta debe ser un número.",
        },
    )


class AnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source="question.text", read_only=True)
    question_order = serializers.IntegerField(source="question.order", read_only=True)
    value_label = serializers.SerializerMethodField()

    class Meta:
        model = Answer
        fields = ("question", "question_order", "question_text", "value", "value_label")

    def get_value_label(self, obj) -> str:
        return dict(SCALE)[obj.value]


class EvaluationListSerializer(serializers.ModelSerializer):
    level_display = serializers.CharField(source="get_level_display", read_only=True)

    class Meta:
        model = Evaluation
        fields = ("id", "created_at", "total_score", "max_score", "percentage", "level", "level_display", "needs_support")


class EvaluationDetailSerializer(EvaluationListSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    interpretation = serializers.SerializerMethodField()

    class Meta(EvaluationListSerializer.Meta):
        fields = EvaluationListSerializer.Meta.fields + ("dimension_scores", "interpretation", "answers")

    def get_interpretation(self, obj) -> dict:
        return interpretation(obj)


class EvaluationCreateSerializer(serializers.Serializer):
    """CA3: deben responderse todas las preguntas activas, una sola vez cada una."""

    answers = AnswerInputSerializer(
        many=True,
        allow_empty=False,
        error_messages={"empty": "Debes responder las preguntas.", "required": "Debes responder las preguntas."},
    )

    def validate_answers(self, answers):
        questions = {q.id: q for q in Question.objects.filter(is_active=True)}
        given = [a["question"] for a in answers]

        unknown = sorted(set(given) - set(questions))
        if unknown:
            raise serializers.ValidationError(f"Preguntas no válidas: {', '.join(map(str, unknown))}.")
        if len(given) != len(set(given)):
            raise serializers.ValidationError("Cada pregunta debe responderse una sola vez.")
        missing = sorted(questions[qid].order for qid in set(questions) - set(given))
        if missing:
            raise serializers.ValidationError(
                f"Faltan respuestas para las preguntas: {', '.join(map(str, missing))}."
            )
        return [(questions[a["question"]], a["value"]) for a in answers]

    @transaction.atomic
    def create(self, validated_data):
        pairs = validated_data["answers"]
        evaluation = Evaluation.objects.create(user=self.context["request"].user, **score_answers(pairs))
        Answer.objects.bulk_create(Answer(evaluation=evaluation, question=q, value=v) for q, v in pairs)
        return evaluation
