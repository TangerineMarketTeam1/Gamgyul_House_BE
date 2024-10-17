from django.db.models import Q
from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters

User = get_user_model()


class ProfileFilter(filters.FilterSet):
    """
    username, email로 필터
    """

    q = filters.CharFilter(method="filter_search", label="Search query")

    class Meta:
        model = User
        fields = ["q"]

    def filter_search(self, queryset, name, value):
        """value가 없을 때 빈 queryset을 반환"""
        if value:
            return (
                queryset.filter(
                    Q(username__icontains=value) | Q(email__icontains=value)
                )
                .exclude(id=self.request.user.id)
                .distinct()
            )
        return queryset.none()
