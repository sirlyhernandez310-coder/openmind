from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import EmergencyChatViewSet, ServiceInfoView

app_name = "emergency"

router = DefaultRouter()
router.register("chats", EmergencyChatViewSet, basename="chat")

urlpatterns = [path("info/", ServiceInfoView.as_view(), name="info"), *router.urls]
