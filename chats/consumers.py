import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from chats.models import ChatRoom, Message, WebSocketConnection

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        클라이언트가 WebSocket에 연결할 때 호출
        """
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"

        # room_id가 올바른 UUID 형식인지 검증
        if not self.is_valid_uuid(self.room_id):
            await self.close()
            return

        # 사용자 인증 여부 확인
        if not self.scope["user"].is_authenticated:
            await self.close()
            return

        # 사용자가 해당 채팅방에 참여 중인지 확인
        if await self.is_user_in_room(self.room_id, self.scope["user"]):
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()

            # WebSocket 연결 정보 기록
            await self.record_connection(self.scope["user"], self.room_id)

            # 읽지 않은 메시지를 모두 읽음 처리
            await self.mark_messages_as_read(self.room_id, self.scope["user"])
        else:
            await self.close()

    async def disconnect(self, close_code):
        """
        WebSocket 연결 종료 시 호출
        """
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.mark_connection_as_disconnected(self.scope["user"], self.room_id)

    async def receive(self, text_data):
        """
        클라이언트로부터 메시지를 수신할 때 호출
        """
        text_data_json = json.loads(text_data)
        message = text_data_json.get("message")
        message_id = text_data_json.get("message_id")

        if message:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "message_id": message_id,
                    "status": "received",
                },
            )
            # 메시지 수신 후 읽음 처리
            await self.mark_messages_as_read(self.room_id, self.scope["user"])

        if message_id:
            await self.mark_message_as_read(message_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "message_read", "message_id": message_id, "is_read": True},
            )

    async def chat_message(self, event):
        """
        메시지를 클라이언트에 전송
        """
        message = event.get("message")
        message_id = event.get("message_id")

        await self.send(
            text_data=json.dumps(
                {
                    "message": message,
                    "message_id": message_id,
                    "status": "received",
                }
            )
        )

    async def message_read(self, event):
        """
        메시지가 읽음 처리되었을 때 클라이언트에 알림
        """
        message_id = event["message_id"]
        is_read = event["is_read"]

        await self.send(
            text_data=json.dumps(
                {"message_id": message_id, "is_read": is_read, "status": "read"}
            )
        )

    @database_sync_to_async
    def is_user_in_room(self, room_id, user):
        """
        데이터베이스에서 사용자가 해당 채팅방에 참여 중인지 확인
        """
        try:
            chat_room = ChatRoom.objects.get(id=room_id)
            return chat_room.participants.filter(id=user.id).exists()
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def record_connection(self, user, room_id):
        """
        WebSocket 연결 정보를 기록
        """
        chat_room = ChatRoom.objects.get(id=room_id)
        WebSocketConnection.objects.create(user=user, chat_room=chat_room)

    @database_sync_to_async
    def mark_connection_as_disconnected(self, user, room_id):
        """
        WebSocket 연결 종료 시간을 기록
        """
        chat_room = ChatRoom.objects.get(id=room_id)
        connection = (
            WebSocketConnection.objects.filter(user=user, chat_room=chat_room)
            .order_by("-connected_at")
            .first()
        )
        if connection:
            connection.mark_disconnected()

    @database_sync_to_async
    def mark_messages_as_read(self, room_id, user):
        """
        사용자가 채팅방에 입장할 때, 읽지 않은 메시지를 모두 읽음 처리
        """
        chat_room = ChatRoom.objects.get(id=room_id)
        Message.objects.filter(chat_room=chat_room, is_read=False).exclude(
            sender=user
        ).update(is_read=True)

    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        """
        실시간 전송된 개별 메시지를 읽음 상태로 업데이트
        """
        try:
            message = Message.objects.get(id=message_id)
            if not message.is_read:
                message.is_read = True
                message.save()
            return message
        except Message.DoesNotExist:
            return None
