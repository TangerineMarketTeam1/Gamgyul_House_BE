from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from chats.models import ChatRoom, Message

User = get_user_model()


class ChatRoomTestCase(APITestCase):
    """
    ChatRoom API 관련 테스트
    """

    def setUp(self):
        """
        테스트용 사용자 생성 및 로그인 처리
        """
        # 데이터 초기화
        ChatRoom.objects.all().delete()
        Message.objects.all().delete()

        # 사용자 생성
        self.user1 = User.objects.create_user(
            email="newuser1@example.com",
            password="newpassword123",
            username="user1",
        )
        self.user2 = User.objects.create_user(
            email="newuser2@example.com",
            password="newpassword123",
            username="user2",
        )
        self.user3 = User.objects.create_user(
            email="newuser3@example.com",
            password="newpassword123",
            username="user3",
        )

        # JWT 토큰 생성 및 헤더에 추가
        self.client = APIClient()
        self.token = RefreshToken.for_user(self.user1).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_chatroom_creation(self):
        """
        채팅방 생성 테스트: 새로운 채팅방이 성공적으로 생성되는지 검증
        """
        url = reverse("chatroom-list")  # router를 통해 자동 생성된 패턴
        data = {"participants": ["user2"]}  # user1은 자동으로 추가됨
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 참가자 이름이 알파벳 순으로 정렬되어야 함
        expected_name = "user1, user2의 대화"
        self.assertEqual(response.data["name"], expected_name)

    def test_duplicate_chatroom_creation(self):
        """
        중복 채팅방 생성 방지 테스트: 동일한 참가자로 두 번째 채팅방 생성 시도 금지
        """
        url = reverse("chatroom-list")
        data = {"participants": ["user2"]}

        # 첫 번째 방 생성
        self.client.post(url, data, format="json")

        # 같은 참가자로 두 번째 생성 시도
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data[0],
            "이미 이 사용자와의 채팅방이 존재합니다.",
        )

    def test_invalid_participants(self):
        """
        유효하지 않은 참가자 처리 테스트: 두 명이 아닌 참가자가 있을 경우 오류 발생.
        """
        url = reverse("chatroom-list")  # router를 통해 자동 생성된 패턴
        data = {"participants": ["user2", "user3"]}  # 세 명 이상일 때

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "1대1 채팅만 가능합니다.")

    def test_chatroom_leave(self):
        """
        채팅방 나가기 테스트: 사용자가 채팅방에서 성공적으로 나갈 수 있는지 검증
        """
        chatroom = ChatRoom.objects.create()
        chatroom.participants.set([self.user1, self.user2])

        url = reverse(
            "chatroom-leave", kwargs={"room_id": chatroom.id}
        )  # 자동 생성된 leave URL

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        chatroom.refresh_from_db()
        self.assertNotIn(self.user1, chatroom.participants.all())

    def test_message_creation(self):
        """
        메시지 생성 테스트: 채팅방에 메시지를 성공적으로 생성하는지 검증
        """
        chatroom = ChatRoom.objects.create()
        chatroom.participants.set([self.user1, self.user2])

        url = reverse(
            "message-list", kwargs={"room_id": chatroom.id}
        )  # 자동 생성된 message list URL
        data = {"content": "Hello!"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["content"], "Hello!")
        self.assertEqual(Message.objects.filter(chat_room=chatroom).count(), 1)

    def test_message_read_on_chatroom_entry(self):
        """
        채팅방 입장 시 메시지 읽음 처리 테스트: 입장 시 기존 메시지가 읽음으로 표시되는지 검증
        """
        chatroom = ChatRoom.objects.create()
        chatroom.participants.set([self.user1, self.user2])

        # 사용자1이 보낸 메시지 (초기 상태에서는 읽지 않음)
        message = Message.objects.create(
            chat_room=chatroom, sender=self.user1, content="Hello!"
        )

        # user2로 로그인하고 채팅방 입장
        self.client.login(email="newuser2@example.com", password="newpassword123")
        url = reverse("chatroom-detail", kwargs={"room_id": chatroom.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 메시지가 읽음 처리되었는지 확인
        message.refresh_from_db()
        self.assertTrue(message.is_read)
