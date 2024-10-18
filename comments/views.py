from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiExample,
)
from .models import Comment
from .serializers import CommentSerializer


class CommentViewSet(viewsets.ModelViewSet):
    """댓글 관련 ViewSet"""

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    @extend_schema(
        summary="댓글 목록 조회 및 작성",
        description="특정 게시물에 대한 댓글을 조회하거나 작성할 수 있습니다.",
        parameters=[
            OpenApiParameter(
                name="post_id", description="게시물의 ID", required=True, type=int
            )
        ],
        responses={
            200: OpenApiResponse(
                description="댓글 목록 조회에 성공하였습니다.",
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="댓글 목록 조회 예시",
                        value=[
                            {
                                "id": 1,
                                "content": "첫 번째 댓글입니다.",
                                "created_at": "2024-10-08T09:00:00Z",
                            },
                            {
                                "id": 2,
                                "content": "두 번째 댓글입니다.",
                                "created_at": "2024-10-08T09:05:00Z",
                            },
                        ],
                    )
                ],
            ),
            201: OpenApiResponse(
                description="댓글 작성에 성공하였습니다.",
                response=CommentSerializer,
            ),
            403: OpenApiResponse(
                description="작성 권한이 없습니다.",
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="작성 권한 없음",
                        value={"detail": "인증된 사용자만 댓글을 작성할 수 있습니다."},
                    )
                ],
            ),
        },
        tags=["comment"],
    )
    def list(self, request, *args, **kwargs):
        """특정 게시물에 대한 댓글 목록 반환"""
        post_id = self.kwargs.get("post_id")
        queryset = self.queryset.filter(post_id=post_id).order_by("-created_at")
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="댓글 작성",
        description="특정 게시물에 대한 댓글을 작성합니다.",
        responses={
            201: OpenApiResponse(
                description="댓글 작성에 성공하였습니다.",
                response=CommentSerializer,
            ),
            403: OpenApiResponse(
                description="작성 권한이 없습니다.",
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="작성 권한 없음",
                        value={"detail": "인증된 사용자만 댓글을 작성할 수 있습니다."},
                    )
                ],
            ),
        },
        tags=["comment"],
    )
    def create(self, request, *args, **kwargs):
        """새 댓글 또는 대댓글 작성"""
        post_id = self.kwargs.get("post_id")
        parent_comment_id = request.data.get("parent_comment", None)

        if parent_comment_id:
            parent_comment = Comment.objects.get(id=parent_comment_id)
            reply_count = Comment.objects.filter(parent_comment=parent_comment).count()
            if reply_count > 2:
                return Response(
                    {"detail": "대댓글은 최대 2개까지 작성할 수 있습니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer, post_id, parent_comment_id)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer, post_id, parent_comment_id):
        if parent_comment_id:
            parent_comment = Comment.objects.get(id=parent_comment_id)
            serializer.save(
                user=self.request.user, post_id=post_id, parent_comment=parent_comment
            )
        else:
            serializer.save(user=self.request.user, post_id=post_id)

    @extend_schema(
        summary="댓글 상세 조회, 수정 및 삭제",
        description="특정 댓글을 조회하거나 수정, 삭제할 수 있습니다. 수정 및 삭제는 작성자만 가능합니다.",
        responses={
            200: OpenApiResponse(description="댓글 조회에 성공하였습니다."),
            403: OpenApiResponse(
                description="수정/삭제 권한이 없습니다.",
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="권한 없음",
                        value={"detail": "댓글 작성자만 수정할 수 있습니다."},
                    )
                ],
            ),
        },
        tags=["comment"],
    )
    def destroy(self, request, *args, **kwargs):
        """댓글 삭제"""
        instance = self.get_object()
        if instance.user != request.user:
            raise PermissionDenied("댓글 작성자만 삭제할 수 있습니다.")

        replies = Comment.objects.filter(parent_comment=instance)
        replies.delete()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
