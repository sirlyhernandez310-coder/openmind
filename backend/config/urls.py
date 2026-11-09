from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

admin.site.site_header = "OpenMind · Administración"
admin.site.site_title = "OpenMind"
admin.site.index_title = "Panel de administración"

urlpatterns = [
    # Portada de la API con el listado de endpoints
    path("", TemplateView.as_view(template_name="accounts/api_home.html"), name="home"),
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/evaluations/", include("apps.evaluations.urls")),
    path("api/professionals/", include("apps.professionals.urls")),
    path("api/emergency/", include("apps.emergency.urls")),
    path("api/appointments/", include("apps.appointments.urls")),
    # Documentación Swagger / OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
