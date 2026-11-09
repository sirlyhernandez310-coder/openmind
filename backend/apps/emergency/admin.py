from django.contrib import admin

from .models import EmergencyChat, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("sender", "text", "created_at")
    can_delete = False


@admin.register(EmergencyChat)
class EmergencyChatAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "psychologist", "status", "created_at", "closed_at")
    list_filter = ("status",)
    search_fields = ("patient__email", "psychologist__email")
    inlines = (MessageInline,)
