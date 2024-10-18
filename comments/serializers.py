from rest_framework import serializers
from .models import Comment
from django.contrib.auth import get_user_model

User = get_user_model()


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "profile_image"]


class CommentSerializer(serializers.ModelSerializer):
    """댓글 모델의 serializer"""

    user = SimpleUserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "user",
            "post",
            "parent_comment",
            "content",
            "created_at",
            "replies",
        ]
        read_only_fields = ["user", "post"]

    def get_replies(self, obj):
        """대댓글 리스트 반환"""
        if obj.parent_comment is None:  # 최상위 댓글인 경우에만 대댓글을 가져옴
            replies = Comment.objects.filter(parent_comment=obj).order_by("-created_at")
            return CommentSerializer(replies, many=True).data
        return []

    def validate(self, attrs):
        """대댓글 작성 시 부모 댓글 유효성 검사"""
        if "parent_comment" in attrs:
            parent_comment = attrs["parent_comment"]
            if not Comment.objects.filter(id=parent_comment.id).exists():
                raise serializers.ValidationError("존재하지 않는 부모 댓글입니다.")
        return attrs
