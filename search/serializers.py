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
    게시물 검색 serializer - 게시물의 모든 정보를 포함
    """

    user = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "user",
            "content",
            "location",
            "created_at",
            "tags",
            "images",
            "likes_count",
            "is_liked",
        ]

    def get_user(self, obj):
        """사용자 정보를 반환합니다."""
        return {
            "id": obj.user.id,
            "username": obj.user.username,
            "profile_image": (
                obj.user.profile_image.url
                if hasattr(obj.user, "profile_image") and obj.user.profile_image
                else None
            ),
        }

    def get_tags(self, obj):
        """태그 목록을 반환합니다."""
        return [tag.name for tag in obj.tags.all()]

    def get_images(self, obj):
        """게시물 이미지 URL 목록을 반환합니다."""
        return [
            image.image.url for image in obj.images.all()
        ]  # related_name 'images' 사용

    def get_likes_count(self, obj):
        """좋아요 수를 반환합니다."""
        return obj.likes.count()

    def get_is_liked(self, obj):
        """현재 사용자의 좋아요 여부를 반환합니다."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def to_representation(self, instance):
        """
        추가적인 에러 처리를 위한 표현 메서드 오버라이드
        """
        try:
            return super().to_representation(instance)
        except Exception as e:
            print(f"Serialization error for post {instance.id}: {str(e)}")
            # 기본 필드만이라도 반환
            return {
                "id": str(instance.id),
                "content": instance.content,
                "location": instance.location,
                "created_at": instance.created_at,
                "user": {
                    "username": instance.user.username,
                    "id": instance.user.id,
                    "profile_image": None,
                },
                "tags": self.get_tags(instance),
                "images": [],
                "likes_count": 0,
                "is_liked": False,
            }


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
