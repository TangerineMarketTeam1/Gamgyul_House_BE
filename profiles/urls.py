from django.urls import path
from . import views

urlpatterns = [
    path(
        "profile/<uuid:id>/",
        views.ProfileDetailView.as_view(),
        name="profile_detail",
    ),
    path("profile/", views.ProfileUpdateView.as_view(), name="profile_update"),
    path(
        "privacy-settings/<uuid:user_id>/",
        views.PrivacySettingsView.as_view(),
        name="privacy_settings",
    ),
]
