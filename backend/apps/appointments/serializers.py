from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework import serializers

from .models import Appointment, Availability
from .slots import is_available, local_tz, session_length

User = get_user_model()


class PersonSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField(source="get_full_name")
    avatar_url = serializers.CharField(allow_null=True)
    specialty = serializers.SerializerMethodField()

    def get_specialty(self, obj) -> str | None:
        profile = getattr(obj, "psychologist_profile", None)
        return profile.get_specialty_display() if profile else None


class AppointmentSerializer(serializers.ModelSerializer):
    psychologist = PersonSerializer(read_only=True)
    patient = PersonSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    start = serializers.SerializerMethodField()
    end = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = ("id", "start", "end", "status", "status_display", "reason", "psychologist", "patient", "created_at")
        read_only_fields = fields

    # fechas en hora de Colombia, con su desfase (-05:00)
    def get_start(self, obj) -> str:
        return obj.start.astimezone(local_tz()).isoformat()

    def get_end(self, obj) -> str:
        return obj.end.astimezone(local_tz()).isoformat()


class AppointmentCreateSerializer(serializers.Serializer):
    """CA1 a CA5 de OM3-17: psicólogo + horario disponible → la cita queda registrada."""

    psychologist = serializers.IntegerField(error_messages={"required": "Selecciona un psicólogo."})
    start = serializers.DateTimeField(
        error_messages={"required": "Selecciona una fecha y un horario.", "invalid": "El horario no es válido."}
    )
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)

    def validate_psychologist(self, value):
        psychologist = (
            User.objects.filter(
                pk=value, role=User.Role.PSICOLOGO, is_active=True, psychologist_profile__is_verified=True
            )
            .select_related("psychologist_profile")
            .first()
        )
        if psychologist is None:
            raise serializers.ValidationError("El psicólogo no existe o no está disponible.")
        return psychologist

    def validate(self, attrs):
        if not is_available(attrs["psychologist"], attrs["start"]):
            raise serializers.ValidationError(
                {"start": "Ese horario ya no está disponible. Elige otro."}, code="slot_taken"
            )
        return attrs

    def create(self, validated_data):
        start = validated_data["start"]
        try:
            with transaction.atomic():
                return Appointment.objects.create(
                    patient=self.context["request"].user,
                    psychologist=validated_data["psychologist"],
                    start=start,
                    end=start + session_length(),
                    reason=validated_data.get("reason", "").strip(),
                )
        except IntegrityError:
            # dos personas reservaron al mismo tiempo: la base de datos solo deja pasar a una
            raise serializers.ValidationError(
                {"start": "Ese horario acaba de ser reservado por otra persona. Elige otro."}
            )


class AvailabilitySerializer(serializers.ModelSerializer):
    weekday_display = serializers.CharField(source="get_weekday_display", read_only=True)

    class Meta:
        model = Availability
        fields = ("id", "weekday", "weekday_display", "start_time", "end_time")
        read_only_fields = ("id", "weekday_display")


class AvailabilityListSerializer(serializers.Serializer):
    """El psicólogo envía su horario semanal completo y reemplaza el anterior."""

    items = AvailabilitySerializer(many=True)

    def validate_items(self, items):
        by_day = {}
        for item in items:
            if item["start_time"] >= item["end_time"]:
                raise serializers.ValidationError("En cada franja la hora de inicio debe ser anterior a la de fin.")
            by_day.setdefault(item["weekday"], []).append((item["start_time"], item["end_time"]))
        for ranges in by_day.values():
            ranges.sort()
            for (_, prev_end), (next_start, _) in zip(ranges, ranges[1:]):
                if next_start < prev_end:
                    raise serializers.ValidationError("Hay franjas que se cruzan en el mismo día.")
        return items
