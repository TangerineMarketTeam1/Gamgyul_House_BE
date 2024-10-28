from django.urls import path, re_path, include
from dj_rest_auth.views import (
    PasswordResetView,
    PasswordResetConfirmView,
    PasswordChangeView,
)
from . import views

urlpatterns = [
    # 기본 인증 및 등록 URLs
    path("", include("dj_rest_auth.urls")),
    path("registration/", include("dj_rest_auth.registration.urls")),
    # 비밀번호 관리
    path("password/reset/", PasswordResetView.as_view(), name="rest_password_reset"),
    re_path(
        r"^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,40})/$",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("password/change/", PasswordChangeView.as_view(), name="rest_password_change"),
    # 소셜 로그인
    path("google/", views.GoogleLogin.as_view(), name="google_login"),
    # 사용자 정보
    path("current-user/", views.CurrentUserView.as_view(), name="current_user"),
]
