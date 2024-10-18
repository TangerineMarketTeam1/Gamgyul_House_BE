from rest_framework.pagination import (
    LimitOffsetPagination,
    PageNumberPagination,
    CursorPagination,
)


class LimitOffsetPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 50


class PageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class CursorPagination(CursorPagination):
    page_size = 10
    cursor_query_param = "cursor"
    ordering = "-created_at"
    max_page_size = 50
