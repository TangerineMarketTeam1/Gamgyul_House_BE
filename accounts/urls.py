from django.urls import path, include
from . import views

urlpatterns = [
    # 기본 인증 및 등록 URLs
    path("", include("dj_rest_auth.urls")),
    path("registration/", include("dj_rest_auth.registration.urls")),
    # 비밀번호 관리
    path(
        "password/change-password/",
        views.PasswordChangeView.as_view(),
        name="password_change",
    ),
    # 소셜 로그인
    path("google/", views.GoogleLogin.as_view(), name="google_login"),
    # 사용자 정보
    path("current-user/", views.CurrentUserView.as_view(), name="current_user"),
    path("user/<str:username>/", views.UserDetailView.as_view(), name="user_detail"),
]
