from django.db.models import Q
from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters
from posts.models import Post
from market.models import Product

User = get_user_model()


class ProfileFilter(filters.FilterSet):
    """사용자 프로필 검색을 위한 필터 세트.

    이 필터는 사용자 이름과 이메일 주소를 기반으로 사용자를 검색합니다.

    Attributes:
        q (CharFilter): 검색 쿼리 필터.
    """

    q = filters.CharFilter(method="filter_search", label="Search query")

    class Meta:
        model = User
        fields = ["q"]

    def filter_search(self, queryset, name, value):
        """검색 쿼리를 기반으로 사용자를 필터링합니다.

        Args:
            queryset (QuerySet): 필터링할 기본 쿼리셋.
            name (str): 필터 이름 (이 메서드에서는 사용되지 않음).
            value (str): 검색 쿼리 문자열.

        Returns:
            QuerySet: 필터링된 사용자 쿼리셋.
        """
        if value:
            return (
                queryset.filter(
                    Q(username__icontains=value) | Q(email__icontains=value)
                )
                .exclude(id=self.request.user.id)
                .distinct()
            )
        return queryset.none()


class PostFilter(filters.FilterSet):
    """게시물 검색을 위한 필터 세트.

    이 필터는 게시물 내용, 사용자 이름, 위치, 그리고 태그를 기반으로 게시물을 검색합니다.

    Attributes:
        q (CharFilter): 검색 쿼리 필터.
    """

    q = filters.CharFilter(method="filter_search", label="Search")

    class Meta:
        model = Post
        fields = ["q"]

    def filter_search(self, queryset, name, value):
        """검색 쿼리를 기반으로 게시물을 필터링합니다.

        Args:
            queryset (QuerySet): 필터링할 기본 쿼리셋.
            name (str): 필터 이름 (이 메서드에서는 사용되지 않음).
            value (str): 검색 쿼리 문자열.

        Returns:
            QuerySet: 필터링된 게시물 쿼리셋.
        """
        words = value.split()
        content_query = Q()
        tag_query = Q()

        for word in words:
            if word.startswith("#"):
                tag_query |= Q(tags__name__iexact=word[1:])
            else:
                content_query |= (
                    Q(content__icontains=word)
                    | Q(user__username__icontains=word)
                    | Q(location__icontains=word)
                )

        return queryset.filter(content_query | tag_query).distinct()


class ProductFilter(filters.FilterSet):
    """제품 검색을 위한 필터 세트.

    이 필터는 제품 이름, 설명, 품종, 재배 지역, 가격, 그리고 사용자를 기반으로 제품을 검색합니다.

    Attributes:
        q (CharFilter): 검색 쿼리 필터.
        category (ChoiceFilter): 검색 카테고리 선택 필터.
        min_price (NumberFilter): 최소 가격 필터.
        max_price (NumberFilter): 최대 가격 필터.
    """

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
        """검색 쿼리와 선택된 카테고리를 기반으로 제품을 필터링합니다.

        Args:
            queryset (QuerySet): 필터링할 기본 쿼리셋.
            name (str): 필터 이름 (이 메서드에서는 사용되지 않음).
            value (str): 검색 쿼리 문자열.

        Returns:
            QuerySet: 필터링된 제품 쿼리셋.
        """
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
        else:
            return queryset.filter(
                Q(name__icontains=value)
                | Q(description__icontains=value)
                | Q(variety__icontains=value)
                | Q(growing_region__icontains=value)
                | Q(user__username__icontains=value)
            )

    def filter_by_category(self, queryset, name, value):
        """카테고리별 필터링을 위한 메서드.

        이 메서드는 현재 구현되어 있지 않으며, 향후 확장을 위해 예약되어 있습니다.

        Args:
            queryset (QuerySet): 필터링할 기본 쿼리셋.
            name (str): 필터 이름.
            value (str): 선택된 카테고리 값.

        Returns:
            QuerySet: 원본 쿼리셋 (현재는 필터링 없음).
        """
        return queryset
