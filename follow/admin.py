from django.contrib import admin
from .models import Follow


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "following", "created_at")
    list_filter = ("created_at",)
    search_fields = (
        "follower__username",
        "follower__email",
        "following__username",
        "following__email",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("follower", "following")
