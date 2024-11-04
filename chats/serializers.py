from django.contrib.auth import get_user_model
from rest_framework import serializers
from chats.models import ChatRoom, Message

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    다른 앱과 Serializer 충돌 방지를 위해 ref_name 설정
    """

    class Meta:
        model = User
        fields = ["id", "username", "email", "profile_image"]
        ref_name = "ChatAppUser"


class ChatRoomSerializer(serializers.ModelSerializer):
    participants = serializers.SlugRelatedField(
        many=True,
        slug_field="username",
        queryset=User.objects.all(),
        required=True,
    )
    name = serializers.CharField(read_only=True)

    class Meta:
        model = ChatRoom
        fields = ["id", "participants", "name", "created_at"]

    def create(self, validated_data):
        """
        새로운 채팅방을 생성하는 로직. 참여자가 2명이어야 하며, room_key로 채팅방을 찾고 관리합니다.
        나갔던 사용자가 다시 들어올 수 있도록 합니다.
        """
        participants = validated_data.pop("participants")

        if len(participants) != 2:
            raise serializers.ValidationError("1대1 채팅만 가능합니다.")

        # 참가자 ID를 정렬한 후 room_key 생성
        participant_ids = sorted([str(participant.id) for participant in participants])
        room_key = "_".join(participant_ids)

        # 동일한 room_key를 가진 채팅방 검색
        existing_room = ChatRoom.objects.filter(room_key=room_key).first()

        if existing_room:
            # 이미 양쪽 다 참여중인 경우
            if all(
                participant in existing_room.participants.all()
                for participant in participants
            ):
                raise serializers.ValidationError(
                    "이미 이 사용자와의 채팅방이 존재합니다."
                )

            # 한 명만 참여중인 경우, 다른 한 명을 다시 추가
            existing_room.participants.add(*participants)
            return existing_room

        # 채팅방이 없는 경우 새로 생성
        chat_room = ChatRoom.objects.create(room_key=room_key)
        chat_room.participants.set(participants)

        return chat_room


class MessageSerializer(serializers.ModelSerializer):
    """
    텍스트 또는 이미지로 메시지 전송 가능
    """

    sender = UserSerializer(read_only=True)
    image = serializers.ImageField(
        max_length=None, allow_empty_file=True, use_url=True, required=False
    )
    sent_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S.%fZ", read_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "content",
            "image",
            "sent_at",
            "is_read",
        ]
        read_only_fields = ["id", "sender", "sent_at", "is_read"]

    def validate(self, data):
        """
        텍스트나 이미지 중 하나는 반드시 포함되어야 합니다.
        """
        content = data.get("content")
        image = data.get("image")
        if not content and not image:
            raise serializers.ValidationError(
                "메시지는 텍스트 또는 이미지를 포함해야 합니다."
            )
        return data

    def validate_image(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "이미지의 크기는 5MB를 넘지 않아야 합니다. 현재 크기: {:.2f}MB".format(
                    value.size / (1024 * 1024)
                )
            )
        return value
