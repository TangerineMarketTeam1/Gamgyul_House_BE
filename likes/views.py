from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
    OpenApiParameter,
    OpenApiTypes,
)
from .models import Post, Like
from .serializers import LikeSerializer


class LikeView(generics.GenericAPIView):
    """
    게시물 좋아요 추가, 취소 및 좋아요 목록 조회를 위한 뷰.

    이 뷰는 인증된 사용자가 게시물에 좋아요를 추가하거나 취소할 수 있게 하며,
    특정 게시물에 좋아요를 누른 사용자 목록을 조회할 수 있게 합니다.

    Attributes:
        serializer_class (LikeSerializer): 좋아요 정보를 직렬화하는 클래스.
        permission_classes (list): 이 뷰에 접근 가능한 권한 클래스 목록.
        queryset (QuerySet): Like 모델의 전체 쿼리셋.
    """

    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]
    queryset = Like.objects.all()

    @extend_schema(
        summary="게시물 좋아요 추가/취소",
        description="게시물에 좋아요를 추가하거나 취소합니다. 응답으로 현재 좋아요 상태와 총 좋아요 수를 반환합니다.",
        parameters=[
            OpenApiParameter(
                name="post_id",
                description="게시물의 UUID",
                required=True,
                type=OpenApiTypes.UUID,
            )
        ],
        responses={
            200: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {
                        "is_liked": {
                            "type": "boolean",
                            "description": "현재 좋아요 상태",
                        },
                        "likes_count": {
                            "type": "integer",
                            "description": "총 좋아요 수",
                        },
                    },
                },
                description="좋아요 처리 결과",
            ),
            404: OpenApiResponse(description="게시물 찾을 수 없음"),
        },
        tags=["like"],
    )
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        like, created = Like.objects.get_or_create(user=request.user, post=post)

        is_liked = created
        if not created:
            like.delete()
            is_liked = False

        likes_count = Like.objects.filter(post=post).count()

        return Response(
            {"is_liked": is_liked, "likes_count": likes_count},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="좋아요를 누른 사용자 목록 조회",
        description="특정 게시물에 좋아요를 누른 사용자들의 목록을 조회합니다.",
        parameters=[
            OpenApiParameter(
                name="post_id",
                description="게시물의 UUID",
                required=True,
                type=OpenApiTypes.UUID,
            )
        ],
        responses={
            200: OpenApiResponse(
                description="사용자 목록 조회 성공",
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="좋아요 사용자 목록 예시",
                        value=[{"username": "user1"}, {"username": "user2"}],
                    )
                ],
            )
        },
        tags=["like"],
    )
    def get_queryset(self):
        """
        특정 게시물에 대한 좋아요 목록을 반환합니다.

        Returns:
            QuerySet: 특정 게시물에 대한 좋아요 QuerySet.
        """
        post_id = self.kwargs["post_id"]
        return Like.objects.filter(post__id=post_id).select_related("user")

    def get(self, request, post_id):
        """
        좋아요를 누른 사용자 목록을 조회합니다.

        Args:
            request (HttpRequest): HTTP 요청 객체.
            post_id (UUID): 조회할 게시물의 UUID.

        Returns:
            Response: 좋아요를 누른 사용자 목록이 포함된 HTTP 응답 객체.

        Raises:
            Http404: 지정된 UUID의 게시물이 존재하지 않을 경우 발생합니다.
        """
        post = get_object_or_404(Post, id=post_id)
        likes = Like.objects.filter(post=post).select_related("user")
        serializer = self.get_serializer(likes, many=True)
        return Response(serializer.data)
