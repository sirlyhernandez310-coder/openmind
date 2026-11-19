from django.contrib import admin

from .models import AdminActionLog


@admin.register(AdminActionLog)
class AdminActionLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "target_email", "reason")
    list_filter = ("action",)
    search_fields = ("target_email", "actor__email")

    # el registro es de solo lectura: nadie puede editarlo ni borrarlo
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
