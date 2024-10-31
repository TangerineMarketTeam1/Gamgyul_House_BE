from django.contrib.auth import get_user_model

from rest_framework import serializers

from accounts.serializers import SimpleUserSerializer
from .models import Comment

User = get_user_model()


class CommentSerializer(serializers.ModelSerializer):
    """댓글 모델을 위한 시리얼라이저.

    Attributes:
        user: 댓글 작성자 정보
        replies: 대댓글 목록
        parent_comment: 부모 댓글 ID (대댓글인 경우)
    """

    user = SimpleUserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    parent_comment = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(), required=False, allow_null=True
    )

    class Meta:
        """메타 클래스.

        Attributes:
            model: 댓글 모델
            fields: 직렬화할 필드 목록
            read_only_fields: 읽기 전용 필드 목록
        """

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
        """댓글의 대댓글 목록을 가져옵니다.

        Args:
            obj: 댓글 인스턴스

        Returns:
            list: 대댓글 목록 데이터 (부모 댓글인 경우)
            list: 빈 리스트 (대댓글인 경우)
        """
        if obj.parent_comment is None:
            replies = Comment.objects.filter(parent_comment=obj).order_by("-created_at")
            return CommentSerializer(replies, many=True).data
        return []

    def validate(self, attrs):
        """댓글 데이터를 검증합니다.

        Args:
            attrs: 검증할 데이터 딕셔너리

        Returns:
            dict: 검증된 데이터

        Raises:
            ValidationError: 부모 댓글이 존재하지 않는 경우
            ValidationError: 대댓글에 댓글을 달려고 하는 경우
            ValidationError: 대댓글 개수가 2개를 초과하는 경우
        """
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
        """댓글 인스턴스를 JSON으로 직렬화합니다.

        부모 댓글이 없는 경우 parent_comment 필드를 제거합니다.

        Args:
            instance: 댓글 인스턴스

        Returns:
            dict: 직렬화된 댓글 데이터
        """
        representation = super().to_representation(instance)
        if representation["parent_comment"] is None:
            representation.pop("parent_comment")
        return representation
