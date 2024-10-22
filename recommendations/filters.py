from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters
from posts.models import Post

User = get_user_model()


class FriendRecommendationFilter(filters.FilterSet):
    """친구 추천을 위한 필터 세트.

    이 필터 세트는 다양한 기준(공통 팔로워, 공통 관심사, 인기도)에 따라
    사용자에게 친구를 추천하는 데 사용됩니다.

    Attributes:
        recommendation_type (ChoiceFilter): 추천 유형을 선택하는 필터.
    """

    recommendation_type = filters.ChoiceFilter(
        choices=[
            ("followers", "Common Followers"),
            ("interests", "Common Interests"),
            ("popular", "Popular Users"),
        ],
        method="filter_recommendations",
    )

    class Meta:
        model = User
        fields = ["recommendation_type"]

    def filter_recommendations(self, queryset, name, value):
        """선택된 추천 유형에 따라 사용자를 필터링합니다.

        이 메서드는 'followers', 'interests', 'popular' 중 하나의 value에 따라
        적절한 필터링 로직을 적용합니다.

        Args:
            queryset (QuerySet): 필터링할 초기 쿼리셋.
            name (str): 필터 필드의 이름 (이 경우에는 사용되지 않음).
            value (str): 선택된 추천 유형.

        Returns:
            QuerySet: 필터링된 사용자 쿼리셋.
        """
        user = self.request.user
        following_users = user.following.values_list("following", flat=True)

        if value == "followers":
            return (
                queryset.filter(followers__follower__in=following_users)
                .exclude(id__in=following_users)
                .exclude(id=user.id)
                .annotate(common_count=Count("followers__follower", distinct=True))
                .order_by("-common_count")
            )

        elif value == "interests":
            user_tags = (
                Post.objects.filter(user=user)
                .values_list("tags__name", flat=True)
                .distinct()
            )
            return (
                queryset.filter(post__tags__name__in=user_tags)
                .exclude(id__in=following_users)
                .exclude(id=user.id)
                .annotate(common_tags=Count("post__tags", distinct=True))
                .order_by("-common_tags")
            )

        elif value == "popular":
            return (
                queryset.annotate(followers_count=Count("followers"))
                .exclude(id__in=following_users)
                .exclude(id=user.id)
                .order_by("-followers_count")
            )

        return queryset.none()
