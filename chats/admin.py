from django.contrib import admin
from chats.models import ChatRoom, Message, WebSocketConnection


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)
    filter_horizontal = ("participants",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "chat_room",
        "sender",
        "sent_at",
        "is_read",
    )
    list_filter = ("is_read", "sent_at")
    search_fields = ("chat_room__name", "sender__username", "content")


@admin.register(WebSocketConnection)
class WebSocketConnectionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "chat_room",
        "connected_at",
        "disconnected_at",
    )
    list_filter = ("connected_at", "disconnected_at")
    search_fields = ("user__username", "chat_room__name")
