from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema, OpenApiResponse
from accounts.serializers import SimpleUserSerializer
from .filters import FriendRecommendationFilter

User = get_user_model()


class FriendRecommendationView(generics.ListAPIView):

    serializer_class = SimpleUserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = FriendRecommendationFilter

    @extend_schema(
        summary="친구 추천",
        description="현재 로그인한 사용자에게 최대 15명의 친구를 추천합니다. 추천 기준은 공통 팔로워, 공통 관심사(해시태그), 인기도 등입니다.",
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
        return User.objects.all()
