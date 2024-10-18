from django.urls import path, include
from rest_framework.routers import DefaultRouter
from chats.views import *

router = DefaultRouter()
router.register(r"chatrooms", ChatRoomViewSet, basename="chatrooms")

message_list = MessageViewSet.as_view(
    {
        "get": "list",
        "post": "create",
    }
)

urlpatterns = [
    path("", include(router.urls)),
    path("chatrooms/<uuid:room_id>/messages/", message_list, name="message-list"),
]
