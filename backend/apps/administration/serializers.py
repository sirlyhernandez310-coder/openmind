from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import AdminActionLog

User = get_user_model()


class AdminUserSerializer(serializers.ModelSerializer):
    """OM3-24 CA2: información básica de cada usuario para el administrador."""

    full_name = serializers.CharField(source="get_full_name", read_only=True)
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    avatar_url = serializers.CharField(read_only=True, allow_null=True)
    is_verified = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "email", "full_name", "first_name", "last_name", "phone", "role", "role_display",
            "is_active", "email_verified", "is_verified", "avatar_url", "date_joined", "last_login",
            "privacy_accepted_at",
        )
        read_only_fields = fields

    def get_is_verified(self, obj) -> bool | None:
        if obj.role != User.Role.PSICOLOGO:
            return None
        profile = getattr(obj, "psychologist_profile", None)
        return bool(profile and profile.is_verified)


class UserStatusSerializer(serializers.Serializer):
    is_active = serializers.BooleanField(error_messages={"required": "Indica si la cuenta queda activa o no."})
    reason = serializers.CharField(max_length=300, required=False, allow_blank=True)


class ActionLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True, allow_null=True)
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = AdminActionLog
        fields = ("id", "created_at", "actor_email", "action", "action_display", "target", "target_email", "reason")
        read_only_fields = fields
