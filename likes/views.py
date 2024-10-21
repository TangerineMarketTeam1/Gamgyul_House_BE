from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
    OpenApiParameter,
)
from .models import Post, Like
from .serializers import LikeSerializer


class LikeView(generics.GenericAPIView):
    """좋아요 추가, 취소 view"""

    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]

    queryset = Like.objects.all()

    @extend_schema(
        summary="게시물 좋아요 추가/취소",
        description="게시물에 좋아요를 추가하거나 취소할 수 있습니다.",
        parameters=[
            OpenApiParameter(
                name="post_id", description="게시물의 ID", required=True, type=int
            )
        ],
        responses={
            201: OpenApiResponse(description="좋아요 추가 성공"),
            204: OpenApiResponse(description="좋아요 취소 성공"),
            404: OpenApiResponse(description="게시물 찾을 수 없음"),
        },
        tags=["like"],
    )
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        like, created = Like.objects.get_or_create(user=request.user, post=post)

        if created:
            return Response(status=status.HTTP_201_CREATED)
        like.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="좋아요를 누른 사용자 목록 조회",
        description="특정 게시물에 좋아요를 누른 사용자들의 목록을 조회합니다.",
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
        """특정 게시물에 대한 좋아요 목록 반환"""
        post_id = self.kwargs["post_id"]
        return Like.objects.filter(post__id=post_id).select_related("user")

    def get(self, request, post_id):
        """좋아요를 누른 사용자 목록 조회"""
        post = get_object_or_404(Post, id=post_id)
        likes = Like.objects.filter(post=post).select_related("user")
        serializer = self.get_serializer(likes, many=True)
        return Response(serializer.data)
