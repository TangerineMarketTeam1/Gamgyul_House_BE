from django.db.models import Q
from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters
from rest_framework import generics
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
)
from accounts.serializers import SimpleUserSerializer
from .filters import ProfileFilter
from posts.models import Post
from market.models import Product
from .serializers import PostSearchSerializer
from market.serializers import ProductListSerializer

User = get_user_model()


class ProfileSearchView(generics.ListAPIView):
    serializer_class = SimpleUserSerializer
    authentication_classes = [JWTAuthentication]
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
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return User.objects.all()

    def filter_queryset(self, queryset):
        """쿼리 파라미터 'q'가 없을 때 빈 queryset을 반환"""
        filtered_queryset = super().filter_queryset(queryset)
        if not self.request.query_params.get("q"):
            return queryset.none()
        return filtered_queryset


class PostFilter(filters.FilterSet):
    q = filters.CharFilter(method="filter_search", label="Search")

    class Meta:
        model = Post
        fields = ["q"]

    def filter_search(self, queryset, name, value):
        # Split the search query into words
        words = value.split()

        # Prepare a Q object for non-tag words
        content_query = Q()
        # Prepare a Q object for tags
        tag_query = Q()

        for word in words:
            if word.startswith("#"):
                # This is a tag
                tag_query |= Q(tags__name__iexact=word[1:])
            else:
                # This is a regular word
                content_query |= (
                    Q(content__icontains=word)
                    | Q(user__username__icontains=word)
                    | Q(location__icontains=word)
                )

        # Combine both queries
        return queryset.filter(content_query | tag_query).distinct()


class PostSearchView(generics.ListAPIView):
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
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Post.objects.all()

    def filter_queryset(self, queryset):
        """쿼리 파라미터 'q'가 없을 때 빈 queryset을 반환"""
        filtered_queryset = super().filter_queryset(queryset)
        if not self.request.query_params.get("q"):
            return queryset.none()
        return filtered_queryset


class ProductFilter(filters.FilterSet):
    q = filters.CharFilter(method="filter_search", label="Search")
    category = filters.ChoiceFilter(
        choices=[
            ("name", "Name"),
            ("description", "Description"),
            ("variety", "Variety"),
            ("growing_region", "Growing Region"),
            ("price", "Price"),
            ("user", "User"),
        ],
        method="filter_by_category",
        label="Category",
    )
    min_price = filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="price", lookup_expr="lte")

    class Meta:
        model = Product
        fields = ["q", "category", "min_price", "max_price"]

    def filter_search(self, queryset, name, value):
        category = self.data.get("category", "all")

        if category == "name":
            return queryset.filter(name__icontains=value)
        elif category == "description":
            return queryset.filter(description__icontains=value)
        elif category == "variety":
            return queryset.filter(variety__icontains=value)
        elif category == "growing_region":
            return queryset.filter(growing_region__icontains=value)
        elif category == "price":
            try:
                price = float(value)
                return queryset.filter(price=price)
            except ValueError:
                return queryset.none()
        elif category == "user":
            return queryset.filter(user__username__icontains=value)
        else:  # 'all' or any other value
            return queryset.filter(
                Q(name__icontains=value)
                | Q(description__icontains=value)
                | Q(variety__icontains=value)
                | Q(growing_region__icontains=value)
                | Q(user__username__icontains=value)
            )

    def filter_by_category(self, queryset, name, value):
        # This method is not actually used, but is required by django-filter
        return queryset


class ProductSearchView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    filterset_class = ProductFilter
    ordering_fields = ["created_at", "price"]
    ordering = ["-created_at"]

    @extend_schema(
        summary="상품 검색",
        description="상품 이름, 설명, 품종, 재배 지역, 가격, 사용자 이름을 기반으로 상품을 검색합니다. 카테고리를 지정하여 검색할 수 있습니다.",
        parameters=[
            OpenApiParameter(
                name="q",
                description="검색 쿼리",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="category",
                description="검색 카테고리 (name, description, variety, growing_region, price, user, all)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="min_price",
                description="최소 가격",
                required=False,
                type=float,
            ),
            OpenApiParameter(
                name="max_price",
                description="최대 가격",
                required=False,
                type=float,
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
                        "price": "10000.00",
                        "user": "johndoe",
                        "stock": 100,
                        "image": "http://example.com/media/products/sample.jpg",
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
