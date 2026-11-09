from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Dimension(models.TextChoices):
    ANIMO = "ANIMO", "Estado de ánimo"
    ANSIEDAD = "ANSIEDAD", "Ansiedad"
    ESTRES = "ESTRES", "Estrés"
    SUENO_ENERGIA = "SUENO_ENERGIA", "Sueño y energía"


class Level(models.TextChoices):
    ESTABLE = "ESTABLE", "Bienestar estable"
    LEVE = "LEVE", "Malestar leve"
    MODERADO = "MODERADO", "Malestar moderado"
    ALTO = "ALTO", "Malestar alto"


# Escala de respuesta (últimas dos semanas)
SCALE = (
    (0, "Nunca"),
    (1, "Algunos días"),
    (2, "Más de la mitad de los días"),
    (3, "Casi todos los días"),
)
MAX_VALUE = SCALE[-1][0]


class Question(models.Model):
    text = models.CharField("pregunta", max_length=255)
    dimension = models.CharField("dimensión", max_length=20, choices=Dimension.choices)
    order = models.PositiveSmallIntegerField("orden", unique=True)
    # si se responde con el valor máximo se recomienda buscar apoyo inmediato
    is_critical = models.BooleanField("pregunta de alerta", default=False)
    is_active = models.BooleanField("activa", default=True)

    class Meta:
        verbose_name = "pregunta"
        verbose_name_plural = "preguntas"
        ordering = ("order",)

    def __str__(self):
        return f"{self.order}. {self.text}"


class Evaluation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="evaluations", verbose_name="usuario"
    )
    created_at = models.DateTimeField("fecha", auto_now_add=True)
    total_score = models.PositiveSmallIntegerField("puntaje")
    max_score = models.PositiveSmallIntegerField("puntaje máximo")
    percentage = models.PositiveSmallIntegerField("porcentaje de malestar")
    level = models.CharField("nivel", max_length=20, choices=Level.choices)
    dimension_scores = models.JSONField("resultado por dimensión", default=dict)
    needs_support = models.BooleanField("requiere apoyo", default=False)

    class Meta:
        verbose_name = "evaluación"
        verbose_name_plural = "evaluaciones"
        ordering = ("-created_at", "-id")

    def __str__(self):
        return f"{self.user.email} · {self.get_level_display()} · {self.created_at:%Y-%m-%d}"


class Answer(models.Model):
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.PROTECT, related_name="answers")
    value = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(MAX_VALUE)])

    class Meta:
        verbose_name = "respuesta"
        verbose_name_plural = "respuestas"
        ordering = ("question__order",)
        constraints = [
            models.UniqueConstraint(fields=("evaluation", "question"), name="unique_answer_per_question"),
        ]
