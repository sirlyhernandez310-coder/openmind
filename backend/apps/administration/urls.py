from django.urls import path

from . import views

app_name = "administration"

urlpatterns = [
    path("users/", views.AdminUserListView.as_view(), name="users"),
    path("users/<int:pk>/", views.AdminUserDetailView.as_view(), name="user-detail"),
    path("users/<int:pk>/status/", views.AdminUserStatusView.as_view(), name="user-status"),
    path("logs/", views.ActionLogListView.as_view(), name="logs"),
    path("stats/", views.StatsView.as_view(), name="stats"),
]
