import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class ChatRoom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True)
    participants = models.ManyToManyField(User, related_name="chat_rooms")
    room_key = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Chat Room"
        verbose_name_plural = "Chat Rooms"

    def save(self, *args, **kwargs):
        """
        참여자 이름을 알파벳 순으로 정렬하여 채팅방 이름을 생성.
        """
        super().save(*args, **kwargs)
        participant_names = ", ".join(
            sorted(user.username for user in self.participants.all())
        )
        self.name = f"{participant_names}의 대화"
        super().save(update_fields=["name"])

    def __str__(self):
        return self.name


class Message(models.Model):
    chat_room = models.ForeignKey(
        ChatRoom, related_name="messages", on_delete=models.CASCADE
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(
        upload_to="chat_images/%Y/%m/%d/",  # S3 업로드 경로
        blank=True,
        null=True,
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"{self.sender.username}님의 메시지"


class WebSocketConnection(models.Model):
    """
    WebSocket 연결 정보를 저장
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="ws_connections"
    )
    chat_room = models.ForeignKey(
        ChatRoom, related_name="ws_connections", on_delete=models.CASCADE
    )
    connected_at = models.DateTimeField(auto_now_add=True)
    disconnected_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} in {self.chat_room} - connected at {self.connected_at}"

    def mark_disconnected(self):
        """
        WebSocket 연결 종료 처리
        """
        self.disconnected_at = timezone.now()
        self.save(update_fields=["disconnected_at"])

    @staticmethod
    def mark_all_messages_as_read(chat_room, user):
        """
        웹소켓 연결 시 읽지 않은 메시지를 읽음 처리
        """
        unread_messages = chat_room.messages.filter(is_read=False).exclude(sender=user)
        for message in unread_messages:
            message.is_read = True
            message.save(update_fields=["is_read"])

    @classmethod
    def get_active_connections(cls, chat_room):
        """
        현재 활성 상태인 WebSocket 연결 목록을 반환
        """
        return cls.objects.filter(chat_room=chat_room, disconnected_at__isnull=True)
