from django.urls import path

from . import views

app_name = "professionals"

urlpatterns = [
    path("register/", views.ProfessionalRegisterView.as_view(), name="register"),
    path("specialties/", views.SpecialtyListView.as_view(), name="specialties"),
    path("me/", views.MyProfileView.as_view(), name="me"),
    path("directory/", views.DirectoryListView.as_view(), name="directory"),
    path("directory/<int:user_id>/", views.DirectoryDetailView.as_view(), name="directory-detail"),
    path("", views.ProfessionalListView.as_view(), name="list"),
    path("<int:pk>/verify/", views.VerifyProfessionalView.as_view(), name="verify"),
]
