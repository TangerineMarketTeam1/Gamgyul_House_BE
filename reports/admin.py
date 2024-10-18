from django.contrib import admin
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """
    신고된 필드는 admin이 수정 불가
    status, comment만 가능
    """

    list_display = (
        "id",
        "reporter",
        "content_type",
        "object_id",
        "reason",
        "status",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "reason", "content_type")
    search_fields = ("reporter__username", "description", "admin_comment")
    readonly_fields = (
        "reporter",
        "content_type",
        "object_id",
        "reason",
        "description",
        "created_at",
    )
    fields = (
        "reporter",
        "content_type",
        "object_id",
        "reason",
        "description",
        "status",
        "admin_comment",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False
