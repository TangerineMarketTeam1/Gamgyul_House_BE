from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class ProfileSearchSerializer(serializers.ModelSerializer):
    """
    프로필 검색 serializer
    """

    class Meta:
        model = User
        fields = ["id", "username", "profile_image"]
