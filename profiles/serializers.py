from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import InMemoryUploadedFile
from market.models import Product
from market.serializers import ProductSerializer
from follow.serializers import FollowSerializer
from .models import PrivacySettings
from posts.models import Post
from follow.models import Follow

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    """
    프로필 정보 표시
    기본 정보, 마켓 정보, 팔로우 관계와 수, 댓글 단 post 내용
    get_<field명> 메서드로 데이터 직렬화
    """

    id = serializers.UUIDField(format="hex_verbose")
    followers = serializers.SerializerMethodField()
    following = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()
    posts = serializers.SerializerMethodField()
    is_self = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "bio",
            "profile_image",
            "followers",
            "following",
            "followers_count",
            "following_count",
            "products",
            "posts",
            "is_self",
        )

    def get_is_self(self, obj):
        """
        프로필 수정 시 자신과 구분하는 메서드
        업데이트 시 자신과 구분
        """
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj == request.user
        return False

    @extend_schema_field(OpenApiTypes.UUID)
    def get_id(self, obj):
        return obj.id

    @extend_schema_field(FollowSerializer(many=True))
    def get_followers(self, obj):
        followers = obj.followers.all().select_related("follower")
        return FollowSerializer(
            [follow.follower for follow in followers], many=True
        ).data

    @extend_schema_field(FollowSerializer(many=True))
    def get_following(self, obj):
        following = obj.following.all().select_related("following")
        return FollowSerializer(
            [follow.following for follow in following], many=True
        ).data

    @extend_schema_field(OpenApiTypes.INT)
    def get_followers_count(self, obj):
        return obj.followers.count()

    @extend_schema_field(OpenApiTypes.INT)
    def get_following_count(self, obj):
        return obj.following.count()

    @extend_schema_field(ProductSerializer(many=True))
    def get_products(self, obj):
        products = Product.objects.filter(user=obj)
        return ProductSerializer(products, many=True, context=self.context).data

    @extend_schema_field(serializers.ListSerializer(child=serializers.DictField()))
    def get_posts(self, obj):
        from posts.serializers import PostSerializer

        posts = Post.objects.filter(user=obj)
        return PostSerializer(posts, many=True, context=self.context).data

    def get_viewer_type(self, viewer, profile_owner):
        """
        프로필 열람 타입 구분 메서드
        """
        is_follower = Follow.objects.filter(
            follower=viewer, following=profile_owner
        ).exists()
        is_following = Follow.objects.filter(
            follower=profile_owner, following=viewer
        ).exists()

        if is_follower:
            return "followers"
        elif is_following:
            return "following"
        else:
            return "others"

    def to_representation(self, instance):
        """
        요청한 사용자가 프로필 소유자가 아닌 경우 프라이버시 설정을 적용
        """
        data = super().to_representation(instance)
        request = self.context.get("request")
        if request and request.user != instance:
            viewer_type = self.get_viewer_type(request.user, instance)
            privacy_settings = PrivacySettings.objects.get_or_create(user=instance)[0]

            fields_to_check = {
                "email": "email",
                "bio": "bio",
                "followers": "follower_list",
                "following": "following_list",
                "products": "posts",
                "posts": "posts",
            }

            for field, setting in fields_to_check.items():
                if not privacy_settings.get_visibility(setting, viewer_type):
                    data.pop(field, None)

            always_visible = [
                "id",
                "username",
                "profile_image",
            ]
            data = {k: v for k, v in data.items() if k in always_visible or k in data}

        return data


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    프로필 업데이트 serializer
    """

    class Meta:
        model = User
        fields = [
            "username",
            "bio",
            "profile_image",
        ]
        extra_kwargs = {
            "username": {"required": False},
            "profile_image": {"required": False},
        }

    def validate_username(self, value):
        """현재 사용자를 제외한 유저들의 username 체크"""
        if User.objects.exclude(pk=self.instance.pk).filter(username=value).exists():
            raise serializers.ValidationError("이 사용자명은 이미 사용 중입니다.")
        return value

    def update(self, instance, validated_data):
        """
        업데이트된 이미지 파일 받아옴
        기존 프로필이 있다면 제거 후 생성
        다른 필드도 업데이트
        """
        profile_image = validated_data.get("profile_image")
        if profile_image and isinstance(profile_image, InMemoryUploadedFile):
            if instance.profile_image:
                instance.profile_image.delete(save=False)
            instance.profile_image = profile_image

        instance.bio = validated_data.get("bio", instance.bio)
        instance.username = validated_data.get("username", instance.username)

        instance.save()
        return instance


class PrivacySettingsSerializer(serializers.ModelSerializer):
    """
    프로필 설정 serializer
    """

    privacy_settings = serializers.JSONField()

    class Meta:
        model = PrivacySettings
        fields = ("privacy_settings",)

    def validate_privacy_settings(self, value):
        """
        privacy_settings의 구조와 값을 검증합니다.
        """
        valid_fields = PrivacySettings.VISIBILITY_FIELDS
        valid_audiences = [choice[0] for choice in PrivacySettings.PRIVACY_CHOICES]

        for field, audiences in value.items():
            if field not in valid_fields:
                raise serializers.ValidationError(f"잘못된 필드 이름: {field}")

            for audience, is_visible in audiences.items():
                if audience not in valid_audiences:
                    raise serializers.ValidationError(f"잘못된 대상 그룹: {audience}")

                if not isinstance(is_visible, bool):
                    raise serializers.ValidationError(
                        f"{field}의 {audience} 값은 불리언이어야 합니다."
                    )

        return value

    def to_representation(self, instance):
        """
        PrivacySettings 인스턴스를 직렬화된 표현으로 변환합니다.
        """
        return {"privacy_settings": instance.privacy_settings}

    def update(self, instance, validated_data):
        """
        PrivacySettings 인스턴스를 업데이트합니다.
        """
        privacy_settings = validated_data.get("privacy_settings", {})

        for field, audiences in privacy_settings.items():
            for audience, is_visible in audiences.items():
                instance.set_visibility(field, audience, is_visible)

        instance.save()
        return instance

    def get_visible_fields(self, viewer_type):
        """
        주어진 viewer_type에 대해 볼 수 있는 필드를 반환합니다.
        """
        if viewer_type not in [choice[0] for choice in PrivacySettings.PRIVACY_CHOICES]:
            raise serializers.ValidationError("잘못된 뷰어 유형입니다.")

        visible_fields = []
        for field in PrivacySettings.VISIBILITY_FIELDS:
            if self.instance.get_visibility(field, viewer_type):
                visible_fields.append(field)

        return visible_fields
