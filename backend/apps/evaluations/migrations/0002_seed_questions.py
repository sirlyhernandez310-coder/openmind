from django.db import migrations

# Cuestionario de bienestar emocional de OpenMind (12 preguntas, 4 dimensiones).
QUESTIONS = [
    ("ANIMO", "Me he sentido triste, decaído(a) o desanimado(a).", False),
    ("ANIMO", "He perdido el interés o el gusto por actividades que antes disfrutaba.", False),
    ("ANIMO", "Me he sentido sin esperanza sobre el futuro.", True),
    ("ANSIEDAD", "Me he sentido nervioso(a), ansioso(a) o con los nervios de punta.", False),
    ("ANSIEDAD", "No he podido dejar de preocuparme o controlar mis preocupaciones.", False),
    ("ANSIEDAD", "He sentido miedo de que algo malo pueda pasar.", False),
    ("ESTRES", "Me he sentido abrumado(a) por mis responsabilidades.", False),
    ("ESTRES", "Me he irritado o enojado con facilidad.", False),
    ("ESTRES", "Me ha costado relajarme o desconectarme.", False),
    ("SUENO_ENERGIA", "He tenido problemas para dormir o he dormido demasiado.", False),
    ("SUENO_ENERGIA", "Me he sentido cansado(a) o con poca energía.", False),
    ("SUENO_ENERGIA", "Me ha costado concentrarme en lo que hago.", False),
]


def seed(apps, schema_editor):
    Question = apps.get_model("evaluations", "Question")
    for order, (dimension, text, critical) in enumerate(QUESTIONS, start=1):
        Question.objects.update_or_create(
            order=order, defaults={"dimension": dimension, "text": text, "is_critical": critical}
        )


def unseed(apps, schema_editor):
    apps.get_model("evaluations", "Question").objects.filter(order__lte=len(QUESTIONS)).delete()


class Migration(migrations.Migration):
    dependencies = [("evaluations", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
