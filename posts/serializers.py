from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer
from .models import Post, PostImage
from likes.models import Like
from django.contrib.auth import get_user_model
from accounts.serializers import SimpleUserSerializer

User = get_user_model()


class PostImageSerializer(serializers.ModelSerializer):
    """게시물 이미지 모델의 serializer"""

    class Meta:
        model = PostImage
        fields = ["id", "image"]


class PostSerializer(TaggitSerializer, serializers.ModelSerializer):
    """게시물 모델의 serializer"""

    user = SimpleUserSerializer(read_only=True)
    uploaded_images = PostImageSerializer(many=True, read_only=True)
    images = serializers.ListField(
        child=serializers.ImageField(
            max_length=255, allow_empty_file=False, use_url=False
        ),
        write_only=True,
        required=True,
    )
    content = serializers.CharField(required=True)
    tags = TagListSerializerField(required=False)
    is_liked = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "user",
            "content",
            "location",
            "created_at",
            "updated_at",
            "tags",
            "uploaded_images",
            "images",
            "is_liked",
            "likes_count",
        ]
        read_only_fields = [
            "user",
            "created_at",
            "updated_at",
            "is_liked",
            "likes_count",
        ]

    def get_is_liked(self, obj):
        """현재 사용자의 좋아요 여부 확인"""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Like.objects.filter(post=obj, user=request.user).exists()
        return False

    def get_likes_count(self, obj):
        """게시물의 총 좋아요 수 반환"""
        return obj.likes.count()

    def create(self, validated_data):
        """게시물 생성 로직"""
        tags_data = validated_data.pop("tags", None)
        images_data = validated_data.pop("images")

        request = self.context.get("request")
        validated_data["user"] = request.user

        if not images_data:
            raise serializers.ValidationError("이미지는 필수입니다.")
        if len(images_data) > 10:
            raise serializers.ValidationError("이미지는 10개까지 첨부할 수 있습니다.")

        post = Post.objects.create(**validated_data)

        """이미지 저장"""
        for image_data in images_data:
            PostImage.objects.create(post=post, image=image_data)

        """태그 추가"""
        if tags_data:
            post.tags.add(*tags_data)

        return post

    def update(self, instance, validated_data):
        """게시물 수정 로직"""
        tags_data = validated_data.pop("tags", None)

        instance.content = validated_data.get("content", instance.content)
        instance.location = validated_data.get("location", instance.location)
        instance.save()

        """태그 수정"""
        if tags_data is not None:
            instance.tags.set(tags_data)

        """이미지 추가 로직"""
        if validated_data.get("images"):
            current_image_count = instance.images.count()
            new_images_count = len(validated_data["images"])

            if new_images_count + current_image_count > 10:
                raise serializers.ValidationError(
                    "이미지는 10개까지 첨부할 수 있습니다."
                )

            for image_data in validated_data["images"]:
                PostImage.objects.create(post=instance, image=image_data)

        return instance

    def to_representation(self, instance):
        """객체를 JSON으로 변환할 때의 표현 정의"""
        representation = super().to_representation(instance)
        representation["tags"] = [str(tag) for tag in instance.tags.all()]
        representation["images"] = [image.image.url for image in instance.images.all()]
        return representation
