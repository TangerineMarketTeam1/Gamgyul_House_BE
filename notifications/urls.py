from django.urls import path, include
from rest_framework.routers import DefaultRouter
from notifications.views import NotificationViewSet

router = DefaultRouter()
router.register(r"", NotificationViewSet, basename="notifications")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "delete_all/",
        NotificationViewSet.as_view({"delete": "delete_all"}),
        name="notification-delete-all",
    ),
]
