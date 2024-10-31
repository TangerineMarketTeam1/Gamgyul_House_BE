from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Comment
from .serializers import CommentSerializer


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="post_id",
            description="게시물의 UUID",
            required=True,
            type=str,
            location=OpenApiParameter.PATH,
            pattern="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        )
    ],
    tags=["comment"],
)
class CommentViewSet(viewsets.ModelViewSet):
    """댓글 관련 ViewSet"""

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    @extend_schema(
        summary="댓글 목록 조회",
        description="특정 게시물에 대한 댓글을 조회합니다.",
        responses={
            200: OpenApiResponse(
                description="댓글 목록 조회에 성공하였습니다.",
                response=CommentSerializer(many=True),
            ),
        },
    )
    def list(self, request, *args, **kwargs):
        """특정 게시물의 댓글 목록을 반환합니다.

        Args:
            request: HTTP 요청 객체
            *args: 추가 인자
            **kwargs: 키워드 인자 (post_id 포함)

        Returns:
            Response: 댓글 목록 데이터
        """
        post_id = self.kwargs.get("post_id")
        queryset = self.queryset.filter(post_id=post_id).order_by("-created_at")
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="댓글 작성",
        description="특정 게시물에 대한 댓글을 작성합니다.",
        request=CommentSerializer,
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
    )
    def create(self, request, *args, **kwargs):
        """새 댓글 또는 대댓글을 작성합니다.

        Args:
            request: HTTP 요청 객체
            *args: 추가 인자
            **kwargs: 키워드 인자 (post_id 포함)

        Returns:
            Response: 생성된 댓글 데이터와 201 상태코드

        Raises:
            Response: 대댓글 개수 초과시 400 에러
        """
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
        """댓글 생성을 수행합니다.

        Args:
            serializer: 댓글 시리얼라이저 인스턴스
            post_id: 게시물 ID
            parent_comment_id: 부모 댓글 ID (대댓글인 경우)
        """
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
    )
    def destroy(self, request, *args, **kwargs):
        """댓글과 관련 대댓글을 삭제합니다.

        Args:
            request: HTTP 요청 객체
            *args: 추가 인자
            **kwargs: 키워드 인자

        Returns:
            Response: 204 No Content 응답

        Raises:
            PermissionDenied: 댓글 작성자가 아닌 경우
        """
        instance = self.get_object()
        if instance.user != request.user:
            raise PermissionDenied("댓글 작성자만 삭제할 수 있습니다.")

        replies = Comment.objects.filter(parent_comment=instance)
        replies.delete()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        """해당 뷰에 필요한 권한들을 반환합니다.

        Returns:
            list: 필요한 권한 클래스들의 인스턴스 리스트
        """
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
