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
    call_opens_at = serializers.SerializerMethodField(help_text="Desde cuándo se puede entrar a la videollamada")

    class Meta:
        model = Appointment
        fields = (
            "id", "start", "end", "status", "status_display", "reason", "psychologist", "patient", "created_at",
            "call_opens_at",
        )
        read_only_fields = fields

    def get_call_opens_at(self, obj) -> str:
        from .call import call_window

        return call_window(obj)[0].astimezone(local_tz()).isoformat()

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


# ------------------------------------------------------------------ OM3-20 Videollamada
class CallSignalSerializer(serializers.Serializer):
    ACTIONS = ("join", "offer", "answer", "leave")
    action = serializers.ChoiceField(choices=ACTIONS, error_messages={"invalid_choice": "Acción no válida."})
    # trim_whitespace=False: la descripción WebRTC (SDP) debe conservar su salto de línea final
    sdp = serializers.CharField(required=False, allow_blank=True, max_length=20000, trim_whitespace=False)

    def validate(self, attrs):
        if attrs["action"] in ("offer", "answer") and not attrs.get("sdp"):
            raise serializers.ValidationError({"sdp": "Falta la descripción de la conexión."})
        return attrs


class CallStateSerializer(serializers.Serializer):
    appointment = AppointmentSerializer()
    role = serializers.CharField()
    can_join = serializers.BooleanField()
    reason = serializers.CharField(allow_null=True)
    opens_at = serializers.DateTimeField()
    closes_at = serializers.DateTimeField()
    ice_servers = serializers.ListField(child=serializers.DictField())
    offer = serializers.CharField(allow_blank=True)
    offer_at = serializers.DateTimeField(allow_null=True)
    answer = serializers.CharField(allow_blank=True)
    answer_at = serializers.DateTimeField(allow_null=True)
    psychologist_joined_at = serializers.DateTimeField(allow_null=True)
    patient_joined_at = serializers.DateTimeField(allow_null=True)
