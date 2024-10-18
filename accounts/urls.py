from django.urls import path, re_path
from dj_rest_auth.views import (
    PasswordResetView,
    PasswordResetConfirmView,
    PasswordChangeView,
    LogoutView,
)
from dj_rest_auth.registration.views import RegisterView
from .views import CustomLoginView, GoogleLogin

urlpatterns = [
    path("password/reset/", PasswordResetView.as_view(), name="rest_password_reset"),
    re_path(
        r"^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,40})/$",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("password/change/", PasswordChangeView.as_view(), name="rest_password_change"),
    path("login/", CustomLoginView.as_view(), name="rest_login"),
    path("logout/", LogoutView.as_view(), name="rest_logout"),
    path("registration/", RegisterView.as_view(), name="rest_register"),
    path("google/", GoogleLogin.as_view(), name="google_login"),
]
