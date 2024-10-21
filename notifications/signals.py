from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from chats.models import *
from comments.models import *
from follow.models import *
from likes.models import *
from notifications.models import *


@receiver(post_save, sender=Message)
def create_notification_for_new_message(sender, instance, created, **kwargs):
    if created:
        # 메시지를 보낸 사람을 제외한 모든 참여자에게 알림 생성
        chat_room = instance.chat_room
        recipients = chat_room.participants.exclude(id=instance.sender.id)

        for recipient in recipients:
            # 사용자의 마지막 WebSocket 연결 종료 시간을 가져옴
            last_connection = (
                WebSocketConnection.objects.filter(user=recipient, chat_room=chat_room)
                .order_by("-disconnected_at")
                .first()
            )

            # WebSocket 연결 기록이 없거나, 마지막 연결이 종료된 후 메시지가 온 경우에만 알림 생성
            if not last_connection or (
                last_connection.disconnected_at
                and last_connection.disconnected_at < instance.sent_at
            ):
                notification = Notification.objects.create(
                    recipient=recipient,
                    sender=instance.sender,
                    notification_type="message",
                    message=f"{instance.sender.username}님이 새로운 메시지를 보냈습니다.",
                    related_object_id=instance.id,
                )
                send_notification_via_websocket(
                    Notification, notification, created=True
                )


@receiver(post_save, sender=Comment)
def create_notification_for_new_comment(sender, instance, created, **kwargs):
    """
    새로운 댓글이 달렸을 때 알림을 생성하는 신호
    """
    if created:
        recipient = instance.post.user
        sender = instance.user

        Notification.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type="comment",
            message=f"{sender.username}님이 게시물에 댓글을 남겼습니다.",
            related_object_id=instance.post.id,
        )


@receiver(post_save, sender=Follow)
def create_notification_for_new_follower(sender, instance, created, **kwargs):
    """
    새로운 팔로우가 발생할 때 알림을 생성하는 신호
    """
    if created:
        recipient = instance.following
        sender = instance.follower

        Notification.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type="follow",
            message=f"{sender.username}님이 당신을 팔로우했습니다.",
            related_object_id=None,  # 팔로우는 관련 객체가 없으므로 None
        )


@receiver(post_save, sender=Like)
def create_notification_for_new_like(sender, instance, created, **kwargs):
    """
    좋아요가 눌렸을 때 알림을 생성하는 신호
    """
    if created:
        recipient = instance.post.user
        sender = instance.user

        Notification.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type="like",
            message=f"{sender.username}님이 게시물을 좋아합니다.",
            related_object_id=instance.post.id,
        )


@receiver(post_save, sender=Notification)
def send_notification_via_websocket(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        recipient_id = str(instance.recipient.id)

        async_to_sync(channel_layer.group_send)(
            f"user_{recipient_id}_notifications",
            {"type": "send_notification", "notification": instance.message},
        )
