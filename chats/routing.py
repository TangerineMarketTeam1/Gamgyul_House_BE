from django.urls import re_path
from chats.consumers import *

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_id>[0-9a-f-]+)/$", ChatConsumer.as_asgi()),
]
