import uuid
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
    OpenApiParameter,
)
from .models import Post, PostImage
from accounts.models import CustomUser
from follow.models import Follow
from config.pagination import LimitOffsetPagination, PageNumberPagination
from .serializers import PostSerializer


class PostViewSet(viewsets.ModelViewSet):
    """
    게시물 목록 및 상세 조회, 게시물 CRUD 기능
    비인증 사용자는 게시글 읽기 가능
    인증 사용자는 게시글 생성, 수정, 삭제 가능
    """

    serializer_class = PostSerializer
    parser_classes = (MultiPartParser, FormParser)
    pagination_class = LimitOffsetPagination

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            following_users = Follow.objects.filter(follower=user).values_list(
                "following", flat=True
            )
            if following_users.exists():
                posts = Post.objects.filter(
                    Q(user__in=following_users) | Q(user=user)
                ).order_by("-created_at")
            else:
                posts = Post.objects.filter(user=user).order_by("-created_at")
                popular_users = CustomUser.objects.annotate(
                    followers_count=Count("followers")
                ).order_by("-followers_count")[:10]
                popular_posts = Post.objects.filter(user__in=popular_users)
                posts = posts | popular_posts
        else:
            popular_users = CustomUser.objects.annotate(
                followers_count=Count("followers")
            ).order_by("-followers_count")[:10]
            posts = Post.objects.filter(user__in=popular_users)
        return posts.order_by("-created_at")

    def get_serializer_context(self):
        """
        serializer에 추가적인 context를 제공합니다.
        """
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    @extend_schema(
        summary="게시물 작성",
        description="사용자가 텍스트와 이미지를 포함한 게시물을 작성합니다. ",
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "images": {
                        "type": "array",
                        "items": {"type": "string", "format": "binary"},
                    },
                    "location": {"type": "string"},
                    "tags": {"type": "list"},
                },
                "required": ["content", "images"],
            }
        },
        responses={
            201: OpenApiResponse(
                description="게시물 작성에 성공하였습니다.",
                response=PostSerializer,
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="성공적인 게시물 작성 예시",
                        value={
                            "id": str(uuid.uuid4()),
                            "content": "게시물 내용",
                            "images": "http://example.com/media/posts/image.jpg",
                            "created_at": "2024-10-07T12:00:00Z",
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                description="잘못된 요청 데이터입니다.",
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="잘못된 요청 예시",
                        value={"detail": "필수 필드가 누락되었습니다."},
                    )
                ],
            ),
        },
        tags=["post"],
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=self.request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(
            {"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )

    def retrieve(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, id=kwargs["pk"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(
        summary="게시물 수정",
        description="게시물의 내용을 수정할 수 있습니다. 수정은 작성자만 가능합니다.",
        responses={
            204: OpenApiResponse(
                description="게시물 수정에 성공하였습니다.",
            ),
            403: OpenApiResponse(
                description="수정 권한이 없습니다.",
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="수정 권한 없음",
                        value={"detail": "글 작성자만 수정할 수 있습니다."},
                    )
                ],
            ),
        },
        tags=["post"],
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            raise PermissionDenied("글 작성자만 수정할 수 있습니다.")
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            existing_images = request.data.get("existing_images", [])
            new_images = request.data.getlist("images")
            for image_data in new_images:
                if image_data:
                    PostImage.objects.create(post=instance, image=image_data)
            return Response(serializer.data)
        return Response(
            {"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        summary="게시물 삭제",
        description="게시물을 삭제합니다. 작성자만 삭제할 수 있습니다.",
        responses={
            204: OpenApiResponse(description="게시물 삭제에 성공하였습니다."),
            403: OpenApiResponse(
                description="삭제 권한이 없습니다.",
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="삭제 권한 없음",
                        value={"detail": "글 작성자만 삭제할 수 있습니다."},
                    )
                ],
            ),
            404: OpenApiResponse(
                description="게시물을 찾을 수 없습니다.",
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="게시물 없음",
                        value={"detail": "해당 ID의 게시물을 찾을 수 없습니다."},
                    )
                ],
            ),
        },
        tags=["post"],
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            raise PermissionDenied("글 작성자만 삭제할 수 있습니다.")
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="게시물 목록 조회",
        description=(
            "사용자가 팔로우한 사용자들과 본인의 최신 게시물을 가져옵니다. 팔로우한 사용자가 없을 경우, 본인과 인기 사용자의 게시물을 반환합니다."
        ),
        parameters=[
            OpenApiParameter(
                name="limit",
                description="결과의 최대 수",
                required=False,
                type=int,
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="limit 값 예시",
                        description="최대 10개의 게시물을 반환",
                        value=10,
                    )
                ],
            ),
            OpenApiParameter(
                name="offset",
                description="결과의 시작점",
                required=False,
                type=int,
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="offset 값 예시",
                        description="처음부터가 아닌 5번째 게시물부터 시작",
                        value=5,
                    )
                ],
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="게시물 목록 반환에 성공하였습니다.",
                response={
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},
                        "next": {"type": "string", "nullable": True},
                        "previous": {"type": "string", "nullable": True},
                        "results": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Post"},
                        },
                    },
                },
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="성공적인 응답 예시",
                        description="게시물 목록을 반환합니다.",
                        value={
                            "count": 2,
                            "next": None,
                            "previous": None,
                            "results": [
                                {
                                    "id": str(uuid.uuid4()),
                                    "content": "이것은 첫 번째 게시물입니다.",
                                    "created_at": "2024-10-07T10:00:00Z",
                                },
                                {
                                    "id": str(uuid.uuid4()),
                                    "content": "이것은 두 번째 게시물입니다.",
                                    "created_at": "2024-10-07T12:00:00Z",
                                },
                            ],
                        },
                    )
                ],
            ),
        },
        tags=["post"],
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
