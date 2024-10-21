from rest_framework import serializers
from django.contrib.auth import get_user_model
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
