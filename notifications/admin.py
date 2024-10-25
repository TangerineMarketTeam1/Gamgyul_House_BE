from django.contrib import admin
from notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "notification_type",
        "recipient",
        "sender",
        "created_at",
        "is_read",
    )
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = ("recipient__username", "sender__username", "message")
    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "id",
                    "recipient",
                    "sender",
                    "notification_type",
                    "message",
                    "related_object_id",
                )
            },
        ),
        ("Status", {"fields": ("is_read", "created_at")}),
    )
