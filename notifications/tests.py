import json
from django.urls import reverse, re_path
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from asgiref.sync import sync_to_async
from channels.auth import AuthMiddlewareStack
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from notifications.consumers import NotificationConsumer
from chats.models import *
from comments.models import *
from follow.models import *
from likes.models import *
from notifications.models import *
from posts.models import *

User = get_user_model()


class MockNotificationConsumer(NotificationConsumer):
    """
    WebSocket 연결을 테스트하기 위한 MockNotificationConsumer.
    알림 수신 시 WebSocket이 올바르게 작동하는지 확인합니다.
    """

    async def connect(self):
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        notification = data.get("notification")

        # 알림 메시지 수신 후 전송
        await self.send(
            text_data=json.dumps({"notification": notification, "status": "received"})
        )

    async def disconnect(self, close_code):
        pass


# WebSocket 라우팅 설정
test_application = AuthMiddlewareStack(
    URLRouter(
        [
            re_path(r"ws/notifications/$", MockNotificationConsumer.as_asgi()),
        ]
    )
)


class NotificationTestCase(TransactionTestCase):
    """
    Notification 앱 테스트 케이스
    """

    def setUp(self):
        """
        테스트용 사용자 및 게시글 생성
        """
        self.user1 = User.objects.create_user(
            username="testuser1",
            email="newuser1@example.com",
            password="newpassword123",
        )
        self.user2 = User.objects.create_user(
            username="testuser2",
            email="newuser2@example.com",
            password="newpassword456",
        )

        self.client = APIClient()
        self.client.login(email=self.user1.email, password="newpassword123")

        # Post 객체 생성
        self.post = Post.objects.create(
            content="테스트용 게시글입니다.", user=self.user1
        )

        # 채팅방 생성 및 참가자 설정
        self.chat_room = ChatRoom.objects.create()
        self.chat_room.participants.set([self.user1, self.user2])

    async def test_like_notification_creation(self):
        """
        내 게시글에 좋아요가 달렸을 때 알림 생성 및 WebSocket 전송 테스트
        """

        # 좋아요 생성 (post_save 신호가 자동으로 발동됨)
        await sync_to_async(Like.objects.create)(post=self.post, user=self.user2)

        # 알림 생성 확인
        notification = await sync_to_async(
            Notification.objects.filter(
                recipient=self.user1, notification_type="like"
            ).first
        )()
        self.assertIsNotNone(notification, "알림이 생성되지 않았습니다.")

        # WebSocket 전송 확인
        websocket_url = f"/ws/notifications/"
        communicator = WebsocketCommunicator(test_application, websocket_url)

        connected, _ = await communicator.connect()
        self.assertTrue(
            connected, f"WebSocket 연결에 실패했습니다. 경로: {websocket_url}"
        )

        # WebSocket 메시지 전송 및 알림 수신 확인
        await communicator.send_json_to({"notification": notification.message})
        response = await communicator.receive_json_from()

        self.assertIn("notification", response, "알림 메시지가 수신되지 않았습니다.")
        self.assertEqual(response["notification"], notification.message)

        await communicator.disconnect()

    async def test_comment_notification_creation(self):
        """
        내 게시글에 댓글이 달렸을 때 알림 생성 및 WebSocket 전송 테스트
        """

        # 댓글 생성 (post_save 신호가 자동으로 발동됨)
        comment_instance = await sync_to_async(Comment.objects.create)(
            post=self.post, user=self.user2, content="테스트용 댓글"
        )

        # 생성된 댓글이 제대로 저장되었는지 확인
        self.assertIsNotNone(comment_instance.id, "댓글이 저장되지 않았습니다.")

        # 알림 생성 확인
        notification = await sync_to_async(
            Notification.objects.filter(
                recipient=self.user1, notification_type="comment"
            ).first
        )()
        self.assertIsNotNone(notification, "댓글 알림이 생성되지 않았습니다.")

        # WebSocket 전송 확인
        websocket_url = f"/ws/notifications/"
        communicator = WebsocketCommunicator(test_application, websocket_url)

        connected, _ = await communicator.connect()
        self.assertTrue(
            connected, f"WebSocket 연결에 실패했습니다. 경로: {websocket_url}"
        )

        # WebSocket 메시지 전송 및 알림 수신 확인
        await communicator.send_json_to({"notification": notification.message})
        response = await communicator.receive_json_from()

        self.assertIn(
            "notification", response, "댓글 알림 메시지가 수신되지 않았습니다."
        )
        self.assertEqual(response["notification"], notification.message)

        await communicator.disconnect()

    async def test_follow_notification_creation(self):
        """
        다른 사용자가 나를 팔로우할 때 알림 생성 및 WebSocket 전송 테스트
        """

        # 팔로우 생성 (post_save 신호가 자동으로 발동됨)
        await sync_to_async(Follow.objects.create)(
            follower=self.user2, following=self.user1
        )

        # 알림 생성 확인
        notification = await sync_to_async(
            Notification.objects.filter(
                recipient=self.user1, notification_type="follow"
            ).first
        )()
        self.assertIsNotNone(notification, "팔로우 알림이 생성되지 않았습니다.")

        websocket_url = f"/ws/notifications/"
        communicator = WebsocketCommunicator(test_application, websocket_url)

        connected, _ = await communicator.connect()
        self.assertTrue(
            connected, f"WebSocket 연결에 실패했습니다. 경로: {websocket_url}"
        )

        # WebSocket 메시지 전송 및 알림 수신 확인
        await communicator.send_json_to({"notification": notification.message})
        response = await communicator.receive_json_from()

        self.assertIn(
            "notification", response, "팔로우 알림 메시지가 수신되지 않았습니다."
        )
        self.assertEqual(response["notification"], notification.message)

        await communicator.disconnect()

    async def test_message_notification_creation(self):
        """
        새로운 메시지가 도착했을 때 알림 생성 및 WebSocket 전송 테스트
        """

        # 메시지 생성
        await sync_to_async(Message.objects.create)(
            chat_room=self.chat_room, sender=self.user2, content="Hello!"
        )

        # 알림 생성 확인
        notification = await sync_to_async(
            Notification.objects.filter(
                recipient=self.user1, notification_type="message"
            ).first
        )()
        self.assertIsNotNone(notification, "메시지 알림이 생성되지 않았습니다.")

        websocket_url = f"/ws/notifications/"
        communicator = WebsocketCommunicator(test_application, websocket_url)

        connected, _ = await communicator.connect()
        self.assertTrue(
            connected, f"WebSocket 연결에 실패했습니다. 경로: {websocket_url}"
        )

        # WebSocket 메시지 전송 및 알림 수신 확인
        await communicator.send_json_to({"notification": notification.message})
        response = await communicator.receive_json_from()

        self.assertIn("notification", response, "메시지 알림이 수신되지 않았습니다.")
        self.assertEqual(response["notification"], notification.message)

        await communicator.disconnect()
