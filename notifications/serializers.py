from rest_framework import serializers
from notifications.models import *


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "recipient",
            "sender",
            "notification_type",
            "message",
            "created_at",
            "is_read",
            "related_object_id",
        ]
        read_only_fields = ["id", "created_at", "sender", "is_read"]
