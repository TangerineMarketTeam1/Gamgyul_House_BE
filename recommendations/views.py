from django.contrib.auth import get_user_model

from django_filters import rest_framework as filters
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.serializers import SimpleUserSerializer
from .filters import FriendRecommendationFilter

User = get_user_model()


class FriendRecommendationView(generics.ListAPIView):
    """친구 추천 뷰.

    이 뷰는 현재 로그인한 사용자에게 최대 15명의 친구를 추천합니다.
    추천 기준은 공통 팔로워, 공통 관심사(해시태그), 인기도입니다.

    Attributes:
        serializer_class: 사용자 정보를 직렬화하는데 사용되는 시리얼라이저.
        permission_classes: 뷰에 접근하기 위해 필요한 권한.
        filter_backends: 쿼리셋 필터링에 사용되는 필터 백엔드.
        filterset_class: 쿼리셋 필터링에 사용되는 필터 클래스.
    """

    serializer_class = SimpleUserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = FriendRecommendationFilter

    @extend_schema(
        summary="친구 추천",
        description="현재 로그인한 사용자에게 최대 15명의 친구를 추천합니다. 추천 기준은 공통 팔로워, 공통 관심사(해시태그), 인기도입니다.",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=SimpleUserSerializer(many=True),
                description="추천된 사용자 목록",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="인증되지 않은 사용자",
            ),
        },
        tags=["recommendation"],
    )
    def list(self, request, *args, **kwargs):
        """친구 추천 목록을 반환합니다.

        이 메서드는 세 가지 추천 유형(팔로워, 관심사, 인기도)에 따라 사용자를 필터링하고,
        최대 15명의 추천 사용자 목록을 생성합니다.

        Args:
            request: HTTP 요청 객체.
            *args: 추가 인자.
            **kwargs: 추가 키워드 인자.

        Returns:
            Response: 추천된 사용자 목록을 포함한 HTTP 응답.
        """
        queryset = self.filter_queryset(self.get_queryset())
        recommended_users = set()

        for recommendation_type in ["followers", "interests", "popular"]:
            filtered_queryset = self.filterset_class(
                data={"recommendation_type": recommendation_type},
                queryset=queryset,
                request=request,
            ).qs

            for user in filtered_queryset:
                recommended_users.add(user.id)
                if len(recommended_users) >= 15:
                    break

            if len(recommended_users) >= 15:
                break

        final_recommendations = User.objects.filter(id__in=recommended_users)[:15]
        serializer = self.get_serializer(final_recommendations, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        """전체 사용자 쿼리셋을 반환합니다.

        Returns:
            QuerySet: 모든 User 객체를 포함하는 쿼리셋.
        """
        return User.objects.all()
