from django.contrib import admin
from django.utils import timezone

from .models import PsychologistProfile


@admin.action(description="Marcar como verificados")
def verify(modeladmin, request, queryset):
    queryset.update(is_verified=True, verified_at=timezone.now())


@admin.register(PsychologistProfile)
class PsychologistProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "specialty", "years_experience", "license_number", "is_verified", "created_at")
    list_filter = ("specialty", "is_verified")
    search_fields = ("user__email", "user__first_name", "user__last_name", "license_number")
    actions = (verify,)
