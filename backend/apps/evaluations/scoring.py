"""
Procesamiento de la evaluación emocional (criterio 4 de OM3-12).

Cada respuesta vale de 0 (Nunca) a 3 (Casi todos los días). Más puntos = más malestar.
El porcentaje se calcula sobre el puntaje máximo posible y se clasifica en 4 niveles.
Es una herramienta de autoevaluación orientativa, NO un diagnóstico clínico.
"""
from collections import defaultdict

from .models import MAX_VALUE, Dimension, Level

THRESHOLDS = ((25, Level.ESTABLE), (50, Level.LEVE), (75, Level.MODERADO), (100, Level.ALTO))

LEVEL_INFO = {
    Level.ESTABLE: {
        "summary": "Tus respuestas reflejan un buen equilibrio emocional en las últimas semanas.",
        "recommendations": [
            "Sigue cuidando los hábitos que te hacen bien: descanso, movimiento y tiempo con personas cercanas.",
            "Repite la evaluación cada cierto tiempo para ver tu evolución.",
        ],
    },
    Level.LEVE: {
        "summary": "Hay algunas señales de malestar. Es normal tener días difíciles, y vale la pena prestarles atención.",
        "recommendations": [
            "Reserva momentos cortos del día para pausas activas o respiración consciente.",
            "Habla con alguien de confianza sobre lo que te preocupa.",
            "Vuelve a evaluarte en una o dos semanas para ver cómo cambia.",
        ],
    },
    Level.MODERADO: {
        "summary": "Tus respuestas muestran un malestar que está afectando tu día a día.",
        "recommendations": [
            "Considera agendar una conversación con un psicólogo.",
            "Prioriza el descanso y reduce, en lo posible, las cargas que puedas aplazar.",
            "No tienes que manejarlo solo(a): apóyate en tu red cercana.",
        ],
    },
    Level.ALTO: {
        "summary": "Tus respuestas indican un malestar alto. Mereces recibir apoyo profesional pronto.",
        "recommendations": [
            "Busca acompañamiento psicológico lo antes posible.",
            "Si necesitas hablar ahora, usa el chat de emergencia de OpenMind.",
            "Si sientes que estás en peligro, llama a la Línea 106 o al 123.",
        ],
    },
}

DIMENSION_TIPS = {
    Dimension.ANIMO: "Actividades pequeñas que antes disfrutabas pueden ayudar a recuperar el ánimo.",
    Dimension.ANSIEDAD: "La respiración lenta (inhala 4 s, exhala 6 s) ayuda a bajar la activación.",
    Dimension.ESTRES: "Dividir las tareas en pasos pequeños reduce la sensación de estar abrumado(a).",
    Dimension.SUENO_ENERGIA: "Mantener horarios regulares de sueño mejora la energía y la concentración.",
}


def level_for(percentage):
    for limit, level in THRESHOLDS:
        if percentage <= limit:
            return level
    return Level.ALTO


def percent(score, max_score):
    return round(score * 100 / max_score) if max_score else 0


def score_answers(answers):
    """
    answers: lista de tuplas (question, value).
    Devuelve un dict con todos los campos calculados de la evaluación.
    """
    total = sum(value for _, value in answers)
    max_score = len(answers) * MAX_VALUE
    percentage = percent(total, max_score)

    by_dimension = defaultdict(lambda: [0, 0])
    for question, value in answers:
        by_dimension[question.dimension][0] += value
        by_dimension[question.dimension][1] += MAX_VALUE

    dimension_scores = {}
    for dimension in Dimension:
        if dimension.value not in by_dimension:
            continue
        score, maximum = by_dimension[dimension.value]
        dim_percentage = percent(score, maximum)
        dimension_scores[dimension.value] = {
            "label": dimension.label,
            "score": score,
            "max_score": maximum,
            "percentage": dim_percentage,
            "level": level_for(dim_percentage).value,
        }

    level = level_for(percentage)
    critical = any(question.is_critical and value == MAX_VALUE for question, value in answers)
    return {
        "total_score": total,
        "max_score": max_score,
        "percentage": percentage,
        "level": level.value,
        "dimension_scores": dimension_scores,
        "needs_support": critical or level == Level.ALTO,
    }


def interpretation(evaluation):
    """Texto de resultado que se muestra al usuario."""
    info = LEVEL_INFO[Level(evaluation.level)]
    worst = max(evaluation.dimension_scores.items(), key=lambda item: item[1]["percentage"], default=None)
    tips = list(info["recommendations"])
    if worst and worst[1]["percentage"] > 25:
        tips.append(DIMENSION_TIPS[Dimension(worst[0])])
    return {
        "summary": info["summary"],
        "recommendations": tips,
        "focus_dimension": worst[1]["label"] if worst and worst[1]["percentage"] > 25 else None,
        "disclaimer": (
            "Esta evaluación es orientativa y no reemplaza un diagnóstico profesional."
        ),
    }
