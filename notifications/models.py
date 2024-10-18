import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = (
        ("message", "메시지"),
        ("follow", "팔로우"),
        ("comment", "댓글"),
        ("like", "좋아요"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        User, related_name="notifications", on_delete=models.CASCADE
    )
    sender = models.ForeignKey(
        User,
        related_name="sent_notifications",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    notification_type = models.CharField(
        max_length=20, choices=NOTIFICATION_TYPE_CHOICES
    )
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    related_object_id = models.UUIDField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.recipient.username}에게"

    def get_redirect_url(self):
        """
        알림 타입에 따라 리디렉션할 URL을 반환
        """
        if self.notification_type == "message":
            return reverse(
                "chat:room_detail", kwargs={"room_id": self.related_object_id}
            )

        elif self.notification_type == "follow":
            return reverse(
                "accounts:profile", kwargs={"username": self.sender.username}
            )

        elif self.notification_type == "comment" or self.notification_type == "like":
            return reverse(
                "posts:post_detail", kwargs={"post_id": self.related_object_id}
            )

        return None
