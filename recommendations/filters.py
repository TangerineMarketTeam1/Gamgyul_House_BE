from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters
from posts.models import Post

User = get_user_model()


class FriendRecommendationFilter(filters.FilterSet):
    """
    필터 기능
    팔로워, 관심사, 인기도 타입으로 추천
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
        """
        value == "followers" :

        - 사용자가 팔로우하는 사람들이 팔로우하는 사용자들을 필터
        - 현재 팔로우하고 있거나 자기 자신은 제외
        - 공통 팔로워의 수를 계산하여 많은 순서대로 정렬

        value == "interests" :

        - 현재 사용자의 포스트에 사용된 모든 태그 필터
        - 현재 사용자의 태그를 사용한 포스트를 작성한 사용자들 필터
        - 현재 팔로우하고 있거나 자기 자신은 제외
        - 공통 태그가 가장 많은 순서대로 정렬

        value == "popular" :

        - 모든 사용자의 팔로워 수를 계산
        - 현재 팔로우하고 있거나 자기 자신은 제외
        - 팔로워 수가 많은 순서대로 정렬
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
