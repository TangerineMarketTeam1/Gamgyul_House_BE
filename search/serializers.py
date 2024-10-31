from rest_framework import serializers
from django.contrib.auth import get_user_model
from chats.models import Message
from posts.models import Post

User = get_user_model()


class ProfileSearchSerializer(serializers.ModelSerializer):
    """
    프로필 검색 serializer
    """

    class Meta:
        model = User
        fields = ["id", "username", "profile_image"]


class PostSearchSerializer(serializers.ModelSerializer):
    """
    게시물 검색 serializer
    """

    username = serializers.CharField(source="user.username", read_only=True)
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ["id", "username", "content", "location", "created_at", "tags"]

    def get_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]


class MessageSearchSerializer(serializers.ModelSerializer):
    """
    메시지 검색 serializer
    """

    username = serializers.CharField(source="sender.username", read_only=True)
    profile_image = serializers.ImageField(
        source="sender.profile_image", read_only=True
    )

    class Meta:
        model = Message
        fields = ["id", "username", "content", "sent_at", "profile_image"]
