from rest_framework import serializers

from .models import EmergencyChat, Message


class ParticipantSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField(source="get_full_name")
    avatar_url = serializers.CharField(allow_null=True)
    specialty = serializers.SerializerMethodField()

    def get_specialty(self, obj) -> str | None:
        profile = getattr(obj, "psychologist_profile", None)
        return profile.get_specialty_display() if profile else None


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    sender_role = serializers.SerializerMethodField()
    sender_avatar = serializers.SerializerMethodField()
    is_system = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = (
            "id", "text", "created_at", "sender", "sender_name", "sender_role", "sender_avatar",
            "is_system", "is_mine",
        )
        read_only_fields = fields

    def get_sender_name(self, obj) -> str:
        return obj.sender.get_full_name() if obj.sender else "OpenMind"

    def get_sender_avatar(self, obj) -> str | None:
        return obj.sender.avatar_url if obj.sender else None

    def get_sender_role(self, obj) -> str | None:
        return obj.sender.role if obj.sender else None

    def get_is_system(self, obj) -> bool:
        return obj.sender_id is None

    def get_is_mine(self, obj) -> bool:
        request = self.context.get("request")
        return bool(request and obj.sender_id == request.user.pk)


class MessageCreateSerializer(serializers.Serializer):
    text = serializers.CharField(
        max_length=2000,
        trim_whitespace=True,
        error_messages={
            "required": "Escribe un mensaje.",
            "blank": "Escribe un mensaje.",
            "max_length": "El mensaje no puede superar los 2000 caracteres.",
        },
    )


class ChatSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    patient = ParticipantSerializer(read_only=True)
    psychologist = ParticipantSerializer(read_only=True, allow_null=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = EmergencyChat
        fields = (
            "id", "status", "status_display", "patient", "psychologist",
            "created_at", "taken_at", "closed_at", "last_message",
        )
        read_only_fields = fields

    def get_last_message(self, obj) -> dict | None:
        message = obj.messages.last()
        return MessageSerializer(message, context=self.context).data if message else None
