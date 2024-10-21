from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommentViewSet

router = DefaultRouter()
router.register(
    r"posts/(?P<post_id>[0-9a-f-]+)/comments", CommentViewSet, basename="comment"
)

urlpatterns = [
    path("", include(router.urls)),
]
