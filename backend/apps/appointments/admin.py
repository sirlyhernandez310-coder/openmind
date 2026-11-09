from django.contrib import admin

from .models import Appointment, Availability


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
