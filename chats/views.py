from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from uuid import UUID
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from chats.models import ChatRoom, Message, WebSocketConnection
from chats.serializers import ChatRoomSerializer, MessageSerializer

User = get_user_model()


def get_chat_room_or_404(room_id, user):
    """
    사용자와 room_id를 기준으로 채팅방을 가져오는 함수
    """
    return get_object_or_404(ChatRoom, id=room_id, participants=user)


class ChatRoomViewSet(viewsets.ModelViewSet):
    serializer_class = ChatRoomSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = "room_id"

    def get_queryset(self):
        """
        현재 로그인한 사용자가 참여한 채팅방 목록을 반환
        """
        if getattr(self, "swagger_fake_view", False):
            return ChatRoom.objects.none()
        return self.request.user.chat_rooms.all()

    @extend_schema(
        summary="채팅방 목록 조회",
        description="현재 로그인한 사용자가 속한 채팅방의 목록을 반환합니다.",
        responses={200: ChatRoomSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="채팅방 생성",
        description="요청한 사용자와 다른 1명의 사용자로 1대1 채팅방을 생성합니다.",
        request=ChatRoomSerializer,
        responses={
            201: ChatRoomSerializer,
            400: {
                "description": "잘못된 요청입니다.",
                "status": status.HTTP_400_BAD_REQUEST,
            },
        },
        examples=[
            OpenApiExample(
                "채팅방 생성 예시", value={"participants": ["user2"]}, request_only=True
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        # 시리얼라이저에 현재 사용자 정보 추가
        data = request.data.copy()
        if isinstance(data.get("participants"), list):
            data["participants"].append(request.user.username)
        else:
            data["participants"] = [request.user.username]

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        chat_room = serializer.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="room_id", type=UUID, location="path", description="채팅방 ID"
            )
        ],
        summary="채팅방 상세 조회",
        description="채팅방 ID를 기준으로 채팅방 정보를 반환합니다. 입장 시 읽지 않은 메시지를 모두 읽음으로 처리합니다.",
        responses={
            200: ChatRoomSerializer,
            404: {
                "description": "채팅방을 찾을 수 없습니다.",
                "status": status.HTTP_404_NOT_FOUND,
            },
        },
    )
    def retrieve(self, request, *args, **kwargs):
        chat_room = get_chat_room_or_404(kwargs["room_id"], request.user)
        WebSocketConnection.mark_all_messages_as_read(chat_room, request.user)
        return Response(self.get_serializer(chat_room).data)

    @extend_schema(
        summary="채팅방 나가기",
        description="요청한 사용자가 채팅방에서 나가며, 남은 참여자가 없으면 채팅방을 삭제합니다.",
        responses={204: None, 404: {"description": "채팅방을 찾을 수 없습니다."}},
    )
    @action(detail=True, methods=["delete"], permission_classes=[IsAuthenticated])
    def leave(self, request, *args, **kwargs):
        """
        사용자가 채팅방을 나가고, 채팅방에 다른 사용자가 없다면 삭제
        """
        chat_room = get_chat_room_or_404(kwargs["room_id"], request.user)
        chat_room.participants.remove(request.user)

        if chat_room.participants.count() == 0:
            chat_room.delete()
            return Response({"message": "채팅방이 삭제되었습니다."}, status=204)

        return Response({"message": "채팅방에서 나갔습니다."}, status=204)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        """
        요청한 사용자가 속한 채팅방의 메시지를 반환
        """
        if getattr(self, "swagger_fake_view", False):
            return Message.objects.none()
        return Message.objects.filter(
            chat_room_id=self.kwargs["room_id"],
            chat_room__participants=self.request.user,
        )

    @extend_schema(
        summary="채팅방 메시지 목록 조회",
        description="해당 채팅방의 메시지 목록을 반환합니다.",
        responses={
            200: MessageSerializer(many=True),
            404: {"description": "채팅방을 찾을 수 없습니다."},
        },
        tags=["message"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="채팅방 메시지 생성",
        description="메시지 생성 시 현재 사용자를 발신자로 설정합니다.",
        request=MessageSerializer,
        responses={
            201: MessageSerializer,
            404: {"description": "채팅방을 찾을 수 없습니다."},
        },
        tags=["message"],
    )
    def create(self, request, *args, **kwargs):
        chat_room = get_chat_room_or_404(self.kwargs["room_id"], self.request.user)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 먼저 메시지를 생성하고 저장
        message = serializer.save(sender=self.request.user, chat_room=chat_room)

        # 상대방 찾기
        other_user = chat_room.participants.exclude(id=self.request.user.id).first()

        # WebSocket 연결 상태와 관계없이 기본적으로 is_read는 False로 설정
        message.is_read = False

        # 상대방이 현재 WebSocket으로 연결되어 있는 경우에만 is_read를 True로 설정
        if WebSocketConnection.objects.filter(
            user=other_user, chat_room=chat_room, disconnected_at__isnull=True
        ).exists():
            message.is_read = True

        # 변경사항 저장
        message.save()

        # WebSocket을 통해 메시지 브로드캐스팅
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{chat_room.id}",
            {
                "type": "chat_message",
                "message": {
                    "id": str(message.id),
                    "content": message.content,
                    "sender": {
                        "id": str(message.sender.id),
                        "username": message.sender.username,
                        "email": message.sender.email,
                        "profile_image": (
                            message.sender.profile_image.url
                            if message.sender.profile_image
                            else None
                        ),
                    },
                    "image": message.image.url if message.image else None,
                    "sent_at": message.sent_at.isoformat(),
                    "is_read": message.is_read,
                },
            },
        )

        return Response(serializer.data, status=201)
