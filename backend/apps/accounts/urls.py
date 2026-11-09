from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    # Registro e inicio de sesión
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("refresh/", views.RefreshView.as_view(), name="refresh"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("me/", views.MeView.as_view(), name="me"),
    path("users/", views.UserListView.as_view(), name="users"),
    # Foto de perfil
    path("me/avatar/", views.MyAvatarView.as_view(), name="my-avatar"),
    path("avatars/<uuid:key>/", views.AvatarImageView.as_view(), name="avatar"),
    # Verificación de correo
    path("verify-email/", views.VerifyEmailView.as_view(), name="verify-email"),
    path("verify-email/resend/", views.ResendVerificationView.as_view(), name="verify-email-resend"),
    # Recuperación de contraseña
    path("password-reset/", views.PasswordResetRequestView.as_view(), name="password-reset"),
    path("password-reset/validate/", views.PasswordResetValidateView.as_view(), name="password-reset-validate"),
    path("password-reset/confirm/", views.PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
]
