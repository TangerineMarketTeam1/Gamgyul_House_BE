from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class FollowSerializer(serializers.ModelSerializer):
    """
    팔로우 serializer
    """

    id = serializers.UUIDField(read_only=True)
    username = serializers.CharField(read_only=True)
    profile_image = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "profile_image")
