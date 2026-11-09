from rest_framework.routers import DefaultRouter

from .views import EvaluationViewSet

app_name = "evaluations"

router = DefaultRouter(trailing_slash=True)
router.register("", EvaluationViewSet, basename="evaluation")

urlpatterns = router.urls
