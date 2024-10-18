from django.urls import path, include
from rest_framework.routers import DefaultRouter
from notifications.views import *

router = DefaultRouter()
router.register(r"list", NotificationViewSet, basename="list")

urlpatterns = [
    path("", include(router.urls)),
]
