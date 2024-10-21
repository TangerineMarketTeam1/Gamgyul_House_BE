from rest_framework import serializers
from .models import Comment
from django.contrib.auth import get_user_model
from accounts.serializers import SimpleUserSerializer

User = get_user_model()


class CommentSerializer(serializers.ModelSerializer):
    """댓글 모델의 serializer"""

    user = SimpleUserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    parent_comment = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(), required=False, allow_null=True
    )

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
        parent_comment = attrs.get("parent_comment")
        if parent_comment:
            if not Comment.objects.filter(id=parent_comment.id).exists():
                raise serializers.ValidationError("존재하지 않는 부모 댓글입니다.")
            if parent_comment.parent_comment:
                raise serializers.ValidationError(
                    "대댓글에는 다시 댓글을 달 수 없습니다."
                )
            reply_count = Comment.objects.filter(parent_comment=parent_comment).count()
            if reply_count >= 2:
                raise serializers.ValidationError(
                    "대댓글은 최대 2개까지만 작성할 수 있습니다."
                )
        return attrs

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if representation["parent_comment"] is None:
            representation.pop("parent_comment")
        return representation
