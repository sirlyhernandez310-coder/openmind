import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.evaluations.models import Answer, Evaluation, Question
from apps.evaluations.scoring import score_answers
from apps.professionals.models import PsychologistProfile, Specialty

DEMO_PASSWORD = "OpenMind#2026"
DEMO_USERS = (
    ("paciente@openmind.com", "Valentina", "Paciente", User.Role.PACIENTE),
    ("psicologo@openmind.com", "Andrés", "Psicólogo", User.Role.PSICOLOGO),
    ("admin@openmind.com", "Admin", "OpenMind", User.Role.ADMINISTRADOR),
)
# niveles de malestar aproximados (0-3) de evaluaciones pasadas, de la más antigua a la más reciente
EXTRA_PSYCHOLOGISTS = (
    ("lucia@openmind.com", "Lucía", "Gómez", Specialty.INFANTIL, 5,
     "Trabajo con niños, niñas y adolescentes en manejo de emociones, autoestima y convivencia escolar."),
    ("camilo@openmind.com", "Camilo", "Duarte", Specialty.FAMILIA, 11,
     "Ayudo a parejas y familias a comunicarse mejor y a atravesar duelos, separaciones y cambios."),
)
DEMO_HISTORY = ((42, 2.2), (28, 1.8), (14, 1.2), (5, 0.8))


class Command(BaseCommand):
    help = "Crea usuarios de prueba (uno por rol, contraseña OpenMind#2026) y datos de ejemplo"

    @transaction.atomic
    def handle(self, *args, **options):
        users = {}
        for email, first_name, last_name, role in DEMO_USERS:
            user = User.objects.filter(email=email).first()
            if user:
                self.stdout.write(f"  · {email} ya existe")
            else:
                is_admin = role == User.Role.ADMINISTRADOR
                user = User.objects.create_user(
                    email=email, password=DEMO_PASSWORD, first_name=first_name, last_name=last_name,
                    role=role, is_staff=is_admin, is_superuser=is_admin, email_verified=True,
                )
                self.stdout.write(self.style.SUCCESS(f"  ✓ {email} ({role})"))
            users[role] = user

        PsychologistProfile.objects.get_or_create(
            user=users[User.Role.PSICOLOGO],
            defaults={
                "specialty": Specialty.CLINICA,
                "years_experience": 8,
                "experience": "Atención clínica de adultos y jóvenes. Intervención en crisis.",
                "license_number": "TP-DEMO-0001",
                "university": "Universidad de Antioquia",
                "description": "Psicólogo clínico con enfoque cognitivo-conductual, especializado en ansiedad y manejo del estrés.",
                "is_verified": True,
                "verified_at": timezone.now(),
            },
        )

        for email, first, last, specialty, years, description in EXTRA_PSYCHOLOGISTS:
            if User.objects.filter(email=email).exists():
                continue
            user = User.objects.create_user(
                email=email, password=DEMO_PASSWORD, first_name=first, last_name=last,
                role=User.Role.PSICOLOGO, email_verified=True,
            )
            PsychologistProfile.objects.create(
                user=user, specialty=specialty, years_experience=years, description=description,
                license_number=f"TP-DEMO-{user.pk:04d}", is_verified=True, verified_at=timezone.now(),
            )
            self.stdout.write(self.style.SUCCESS(f"  ✓ {email} (PSICOLOGO de ejemplo)"))

        self.seed_schedules()

        patient = users[User.Role.PACIENTE]
        if not patient.evaluations.exists():
            self.create_demo_history(patient)
            self.stdout.write(self.style.SUCCESS(f"  ✓ {len(DEMO_HISTORY)} evaluaciones de ejemplo para {patient.email}"))

        self.stdout.write(f"Contraseña de todos: {DEMO_PASSWORD}")

    def seed_schedules(self):
        """Horarios de atención de ejemplo para los psicólogos que aún no tienen."""
        from datetime import time

        from apps.appointments.models import Availability

        plans = {
            "psicologo@openmind.com": [(d, time(8), time(12)) for d in range(5)] + [(d, time(14), time(17)) for d in (0, 2, 4)],
            "lucia@openmind.com": [(d, time(13), time(18)) for d in range(5)] + [(5, time(8), time(12))],
            "camilo@openmind.com": [(d, time(9), time(13)) for d in (1, 3)] + [(d, time(15), time(19)) for d in (1, 3)],
        }
        for email, ranges in plans.items():
            user = User.objects.filter(email=email).first()
            if user and not user.availabilities.exists():
                Availability.objects.bulk_create(
                    Availability(psychologist=user, weekday=d, start_time=a, end_time=b) for d, a, b in ranges
                )
                self.stdout.write(self.style.SUCCESS(f"  ✓ horario de atención para {email}"))

    def create_demo_history(self, patient):
        questions = list(Question.objects.filter(is_active=True))
        rng = random.Random(7)
        for days_ago, mean in DEMO_HISTORY:
            pairs = [(q, max(0, min(3, round(rng.gauss(mean, 0.6))))) for q in questions]
            evaluation = Evaluation.objects.create(user=patient, **score_answers(pairs))
            Answer.objects.bulk_create(Answer(evaluation=evaluation, question=q, value=v) for q, v in pairs)
            Evaluation.objects.filter(pk=evaluation.pk).update(created_at=timezone.now() - timedelta(days=days_ago))
