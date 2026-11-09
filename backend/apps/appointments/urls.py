from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "appointments"

router = DefaultRouter()
router.register("", views.AppointmentViewSet, basename="appointment")

urlpatterns = [
    path("availability/", views.MyAvailabilityView.as_view(), name="my-availability"),
    path("psychologists/<int:psychologist_id>/slots/", views.AvailableSlotsView.as_view(), name="slots"),
    *router.urls,
]
