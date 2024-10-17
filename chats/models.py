import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

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

    def __str__(self):
        return self.name if self.name else f"채팅방 {self.id}"


@receiver(post_save, sender=ChatRoom)
def set_chat_room_name(sender, instance, **kwargs):
    """
    채팅방 이름이 비어 있을 때, 참가자가 2명일 경우 자동으로 이름 생성
    """
    # participants가 2명일 때 채팅방 이름 자동 설정
    if not instance.name and instance.participants.count() == 2:
        participant_names = ", ".join(
            [user.username for user in instance.participants.all()]
        )
        instance.name = f"{participant_names}의 대화"
        instance.save()


class Message(models.Model):
    """
    채팅 메시지 및 이미지 저장
    """

    chat_room = models.ForeignKey(
        ChatRoom, related_name="messages", on_delete=models.CASCADE
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)

    # 채팅방별로 이미지를 저장하도록 경로를 동적으로 생성
    image = models.ImageField(
        upload_to=lambda instance, filename: f"chat_images/{instance.chat_room.id}/{filename}",
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
        self.disconnected_at = timezone.now()
        self.save()
