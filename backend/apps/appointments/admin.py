from django.contrib import admin

from .models import Appointment, Availability, CallRoom


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ("psychologist", "weekday", "start_time", "end_time")
    list_filter = ("weekday",)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("start", "patient", "psychologist", "status")
    list_filter = ("status",)
    search_fields = ("patient__email", "psychologist__email")
    date_hierarchy = "start"


@admin.register(CallRoom)
class CallRoomAdmin(admin.ModelAdmin):
    list_display = ("appointment", "psychologist_joined_at", "patient_joined_at", "started_at")
    readonly_fields = ("offer", "answer")
