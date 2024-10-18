from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
)
from .serializers import ProfileSearchSerializer
from .filters import ProfileFilter

User = get_user_model()


class ProfileSearchView(generics.ListAPIView):
    serializer_class = ProfileSearchSerializer
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
        responses={200: ProfileSearchSerializer(many=True)},
        examples=[
            OpenApiExample(
                "응답 예시",
                value=[
                    {
                        "id": 1,
                        "username": "john_doe",
                        "profile_image": "http://example.com/media/profile_images/john.jpg",
                    },
                    {
                        "id": 2,
                        "username": "jane_doe",
                        "profile_image": "http://example.com/media/profile_images/jane.jpg",
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
