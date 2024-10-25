from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters
from rest_framework import generics
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
)
from accounts.serializers import SimpleUserSerializer
from .filters import ProfileFilter, PostFilter, ProductFilter
from posts.models import Post
from market.models import Product
from .serializers import PostSearchSerializer
from market.serializers import ProductListSerializer

User = get_user_model()


class ProfileSearchView(generics.ListAPIView):
    """사용자 프로필 검색을 위한 API 뷰.

    이 뷰는 사용자 이름과 이메일을 기반으로 프로필을 검색하고 결과를 반환합니다.

    Attributes:
        serializer_class (Serializer): 응답 데이터 직렬화를 위한 시리얼라이저.
        permission_classes (list): 뷰 접근 권한 클래스 목록.
        filter_backends (tuple): 사용할 필터 백엔드.
        filterset_class (FilterSet): 쿼리셋 필터링을 위한 필터 클래스.
    """

    serializer_class = SimpleUserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ProfileFilter

    @extend_schema(
        summary="프로필 검색",
        description="사용자 이름, 이메일을 기반으로 프로필을 검색합니다.",
        parameters=[
            OpenApiParameter(
                name="q",
                description="검색 쿼리 (사용자 이름, 이메일)",
                required=False,
                type=str,
            ),
        ],
        responses={200: SimpleUserSerializer(many=True)},
        examples=[
            OpenApiExample(
                "응답 예시",
                value=[
                    {
                        "id": 1,
                        "username": "john_doe",
                        "profile_image": "http://example.com/profile/2024/10/20/jane.jpg",
                    },
                    {
                        "id": 2,
                        "username": "jane_doe",
                        "profile_image": "http://example.com/profile/2024/10/20/jane.jpg",
                    },
                ],
                response_only=True,
            ),
        ],
        tags=["search"],
    )
    def get(self, request, *args, **kwargs):
        """GET 요청을 처리하여 프로필 검색 결과를 반환합니다.

        이 메서드는 부모 클래스의 get 메서드를 호출하여 검색 결과를 반환합니다.

        Args:
            request (HttpRequest): 클라이언트의 HTTP 요청 객체.
            *args: 추가 위치 인자.
            **kwargs: 추가 키워드 인자.

        Returns:
            Response: 검색된 프로필 목록을 포함한 HTTP 응답.
        """
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """검색 대상이 될 기본 쿼리셋을 반환합니다.

        Returns:
            QuerySet: 모든 사용자 객체를 포함하는 쿼리셋.
        """
        return User.objects.all()

    def filter_queryset(self, queryset):
        """쿼리셋에 필터를 적용합니다.

        이 메서드는 검색 쿼리 파라미터('q')가 제공된 경우에만 필터링을 수행합니다.
        검색 쿼리가 없으면 빈 쿼리셋을 반환합니다.

        Args:
            queryset (QuerySet): 필터링할 원본 쿼리셋.

        Returns:
            QuerySet: 필터링된 쿼리셋 또는 빈 쿼리셋.
        """
        filtered_queryset = super().filter_queryset(queryset)
        if not self.request.query_params.get("q"):
            return queryset.none()
        return filtered_queryset


class PostSearchView(generics.ListAPIView):
    """게시물 검색을 위한 API 뷰.


    이 뷰는 게시물 내용, 사용자 이름, 위치, 태그를 기반으로 게시물을 검색하고 결과를 반환합니다.
    검색 결과는 생성 시간의 역순으로 정렬됩니다.

    Attributes:
        serializer_class (Serializer): 응답 데이터 직렬화를 위한 시리얼라이저.
        filter_backends (tuple): 사용할 필터 백엔드.
        filterset_class (FilterSet): 쿼리셋 필터링을 위한 필터 클래스.
        ordering (list): 기본 정렬 기준.
    """

    serializer_class = PostSearchSerializer
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    filterset_class = PostFilter
    ordering = ["-created_at"]

    @extend_schema(
        summary="게시물 검색",
        description="게시물 내용, 사용자 이름, 위치, 태그를 기반으로 게시물을 검색합니다. 태그는 '#'으로 시작하며 띄어쓰기로 구분됩니다.",
        parameters=[
            OpenApiParameter(
                name="q",
                description="검색 쿼리 (게시물 내용, 사용자 이름, 위치, 태그)",
                required=False,
                type=str,
            ),
        ],
        responses={200: PostSearchSerializer(many=True)},
        examples=[
            OpenApiExample(
                "응답 예시",
                value=[
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "username": "john_doe",
                        "content": "This is a sample post content #example",
                        "location": "New York",
                        "created_at": "2024-03-15T12:00:00Z",
                        "tags": ["example"],
                    },
                    {
                        "id": "223e4567-e89b-12d3-a456-426614174001",
                        "username": "jane_doe",
                        "content": "Another example post #sample #test",
                        "location": "Los Angeles",
                        "created_at": "2024-03-16T14:30:00Z",
                        "tags": ["sample", "test"],
                    },
                ],
                response_only=True,
            ),
        ],
        tags=["search"],
    )
    def get(self, request, *args, **kwargs):
        """GET 요청을 처리하여 게시물 검색 결과를 반환합니다.

        이 메서드는 부모 클래스의 get 메서드를 호출하여 검색 결과를 반환합니다.

        Args:
            request (HttpRequest): 클라이언트의 HTTP 요청 객체.
            *args: 추가 위치 인자.
            **kwargs: 추가 키워드 인자.

        Returns:
            Response: 검색된 게시물 목록을 포함한 HTTP 응답.
        """
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """검색 대상이 될 기본 쿼리셋을 반환합니다.

        Returns:
            QuerySet: 모든 게시물 객체를 포함하는 쿼리셋.
        """
        return Post.objects.all()

    def filter_queryset(self, queryset):
        """쿼리셋에 필터를 적용합니다.

        이 메서드는 검색 쿼리 파라미터('q')가 제공된 경우에만 필터링을 수행합니다.
        검색 쿼리가 없으면 빈 쿼리셋을 반환합니다.

        Args:
            queryset (QuerySet): 필터링할 원본 쿼리셋.

        Returns:
            QuerySet: 필터링된 쿼리셋 또는 빈 쿼리셋.
        """
        filtered_queryset = super().filter_queryset(queryset)
        if not self.request.query_params.get("q"):
            return queryset.none()
        return filtered_queryset


class ProductSearchView(generics.ListAPIView):
    """상품 검색을 위한 API 뷰.

    이 뷰는 상품 이름과 사용자 이름을 기반으로 상품을 검색하고 결과를 반환합니다.
    검색 결과는 생성 시간의 역순으로 정렬됩니다.

    Attributes:
        serializer_class (Serializer): 응답 데이터 직렬화를 위한 시리얼라이저.
        filter_backends (tuple): 사용할 필터 백엔드.
        filterset_class (FilterSet): 쿼리셋 필터링을 위한 필터 클래스.
        ordering_fields (list): 정렬 가능한 필드 목록.
        ordering (list): 기본 정렬 기준.
    """

    serializer_class = ProductListSerializer
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    filterset_class = ProductFilter
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    @extend_schema(
        summary="상품 검색",
        description="상품 이름과 사용자 이름을 기반으로 상품을 검색합니다.",
        parameters=[
            OpenApiParameter(
                name="q",
                description="검색 쿼리",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="category",
                description="검색 카테고리 (name, user, all)",
                required=False,
                type=str,
            ),
        ],
        responses={200: ProductListSerializer(many=True)},
        examples=[
            OpenApiExample(
                "응답 예시",
                value=[
                    {
                        "id": 1,
                        "name": "샘플 상품",
                        "user": "johndoe",
                        "stock": 100,
                        "image": "http://example.com/media/products/sample.jpg",
                        "price": 35000,
                    },
                ],
                response_only=True,
            ),
        ],
        tags=["search"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Product.objects.all()

    def filter_queryset(self, queryset):
        filtered_queryset = super().filter_queryset(queryset)
        if not self.request.query_params.get("q"):
            return queryset.none()
        return filtered_queryset
