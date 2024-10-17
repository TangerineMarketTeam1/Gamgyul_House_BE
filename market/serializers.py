from rest_framework import serializers
from .models import Product


class ProductListSerializer(serializers.ModelSerializer):
    """
    상품 리스트 시리얼라이저
    """

    user = serializers.CharField(source="user.username")
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "price", "user", "stock", "image"]

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.images.exists():
            image = obj.images.first()
            return (
                request.build_absolute_uri(image.image.url)
                if request
                else image.image.url
            )
        return None


class ProductSerializer(serializers.ModelSerializer):
    """
    상품 시리얼라이저
    """

    username = serializers.SerializerMethodField()
    user_id = serializers.ReadOnlyField(source="user.id")
    images = serializers.SerializerMethodField()
    user_profile_image = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "user",
            "user_id",
            "username",
            "user_profile_image",
            "price",
            "description",
            "stock",
            "variety",
            "growing_region",
            "harvest_date",
            "created_at",
            "updated_at",
            "images",
        ]
        ref_name = "marketProductSerializer"

    def get_username(self, obj):
        return obj.user.username

    def get_user_profile_image(self, obj):
        request = self.context.get("request")
        if obj.user.profile_image:
            return (
                request.build_absolute_uri(obj.user.profile_image.url)
                if request
                else obj.user.profile_image.url
            )
        return None

    def get_images(self, obj):
        request = self.context.get("request")
        return (
            [request.build_absolute_uri(image.image.url) for image in obj.images.all()]
            if request
            else []
        )
