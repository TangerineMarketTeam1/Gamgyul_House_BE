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
    """사용자 프로필 정보를 직렬화하는 serializer.

    이 serializer는 사용자의 기본 정보, 마켓 정보, 팔로우 관계와 수, 그리고 사용자가 작성한 게시물 내용을 포함합니다.
    대부분의 필드는 get_<field명> 메서드를 통해 커스텀 직렬화됩니다.

    Attributes:
        id (UUIDField): 사용자의 고유 식별자.
        followers (SerializerMethodField): 사용자의 팔로워 목록.
        following (SerializerMethodField): 사용자가 팔로우하는 사용자 목록.
        followers_count (SerializerMethodField): 사용자의 팔로워 수.
        following_count (SerializerMethodField): 사용자가 팔로우하는 사용자 수.
        products (SerializerMethodField): 사용자의 상품 목록.
        posts (SerializerMethodField): 사용자의 게시물 목록.
        is_self (SerializerMethodField): 현재 사용자가 프로필 소유자인지 여부.
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
        """현재 사용자가 프로필 소유자인지 확인합니다.

        이 메서드는 프로필 수정 시 자신과 다른 사용자를 구분하는 데 사용됩니다.

        Args:
            obj (User): 프로필 소유자 객체.

        Returns:
            bool: 현재 사용자가 프로필 소유자인 경우 True, 그렇지 않으면 False.
        """
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj == request.user
        return False

    @extend_schema_field(OpenApiTypes.UUID)
    def get_id(self, obj):
        """사용자의 ID를 반환합니다.

        Args:
            obj (User): 사용자 객체.

        Returns:
            UUID: 사용자의 고유 식별자.
        """
        return obj.id

    @extend_schema_field(FollowSerializer(many=True))
    def get_followers(self, obj):
        """사용자의 팔로워 목록을 반환합니다.

        Args:
            obj (User): 사용자 객체.

        Returns:
            list: 팔로워 사용자 객체의 직렬화된 데이터 목록.
        """
        followers = obj.followers.all().select_related("follower")
        return FollowSerializer(
            [follow.follower for follow in followers], many=True
        ).data

    @extend_schema_field(FollowSerializer(many=True))
    def get_following(self, obj):
        """사용자가 팔로우하는 사용자 목록을 반환합니다.

        Args:
            obj (User): 사용자 객체.

        Returns:
            list: 팔로우하는 사용자 객체의 직렬화된 데이터 목록.
        """
        following = obj.following.all().select_related("following")
        return FollowSerializer(
            [follow.following for follow in following], many=True
        ).data

    @extend_schema_field(OpenApiTypes.INT)
    def get_followers_count(self, obj):
        """사용자의 팔로워 수를 반환합니다.

        Args:
            obj (User): 사용자 객체.

        Returns:
            int: 팔로워 수.
        """
        return obj.followers.count()

    @extend_schema_field(OpenApiTypes.INT)
    def get_following_count(self, obj):
        """사용자가 팔로우하는 사용자 수를 반환합니다.

        Args:
            obj (User): 사용자 객체.

        Returns:
            int: 팔로우하는 사용자 수.
        """
        return obj.following.count()

    @extend_schema_field(ProductSerializer(many=True))
    def get_products(self, obj):
        """사용자의 상품 목록을 반환합니다.

        Args:
            obj (User): 사용자 객체.

        Returns:
            list: 사용자의 상품 객체의 직렬화된 데이터 목록.
        """
        products = Product.objects.filter(user=obj)
        return ProductSerializer(products, many=True, context=self.context).data

    @extend_schema_field(serializers.ListSerializer(child=serializers.DictField()))
    def get_posts(self, obj):
        """사용자의 게시물 목록을 반환합니다.

        Args:
            obj (User): 사용자 객체.

        Returns:
            list: 사용자의 게시물 객체의 직렬화된 데이터 목록.
        """
        from posts.serializers import PostSerializer

        posts = Post.objects.filter(user=obj)
        return PostSerializer(posts, many=True, context=self.context).data

    def get_viewer_type(self, viewer, profile_owner):
        """프로필 열람자의 유형을 결정합니다.

        Args:
            viewer (User): 프로필을 보는 사용자.
            profile_owner (User): 프로필 소유자.

        Returns:
            str: 'followers', 'following', 또는 'others' 중 하나.
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
        """객체의 직렬화된 표현을 반환합니다.

        이 메서드는 프라이버시 설정을 적용하여 요청한 사용자가 프로필 소유자가 아닌 경우
        특정 필드를 제외시킵니다.

        Args:
            instance (User): 직렬화할 사용자 객체.

        Returns:
            dict: 직렬화된 사용자 데이터.
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
    """사용자 프로필 정보를 업데이트하기 위한 serializer.

    이 serializer는 사용자의 username, bio, profile_image를 업데이트하는 데 사용됩니다.
    username과 profile_image 필드는 선택적입니다.

    Attributes:
        username (str): 사용자의 새 사용자명 (선택적).
        bio (str): 사용자의 새 자기소개.
        profile_image (InMemoryUploadedFile): 사용자의 새 프로필 이미지 (선택적).
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
        """username의 유일성을 검증합니다.

        Args:
            value (str): 검증할 username 값.

        Returns:
            str: 유효한 username 값.

        Raises:
            serializers.ValidationError: username이 이미 사용 중인 경우 발생.
        """
        if User.objects.exclude(pk=self.instance.pk).filter(username=value).exists():
            raise serializers.ValidationError("이 사용자명은 이미 사용 중입니다.")
        return value

    def update(self, instance, validated_data):
        """사용자 프로필 정보를 업데이트합니다.

        이 메서드는 검증된 데이터를 사용하여 사용자의 프로필 정보를 업데이트합니다.
        profile_image가 제공된 경우 기존 이미지를 삭제하고 새 이미지로 교체합니다.

        Args:
            instance (User): 업데이트할 사용자 객체.
            validated_data (dict): 검증된 업데이트 데이터.

        Returns:
            User: 업데이트된 사용자 객체.
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
    """사용자의 개인정보 설정을 직렬화 및 역직렬화하는 serializer.

    이 serializer는 사용자의 개인정보 설정을 JSON 필드로 관리합니다.
    각 설정은 필드별로 다양한 대상 그룹에 대한 가시성을 정의합니다.

    Attributes:
        privacy_settings (JSONField): 사용자의 개인정보 설정을 담는 JSON 필드.
    """

    privacy_settings = serializers.JSONField()

    class Meta:
        model = PrivacySettings
        fields = ("privacy_settings",)

    def validate_privacy_settings(self, value):
        """privacy_settings 필드의 유효성을 검사합니다.

        Args:
            value (dict): 검증할 privacy_settings 값.

        Returns:
            dict: 유효한 privacy_settings 값.

        Raises:
            serializers.ValidationError: 잘못된 필드 이름, 대상 그룹 또는 가시성 값인 경우 발생.
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
        """PrivacySettings 인스턴스를 직렬화된 표현으로 변환합니다.

        Args:
            instance (PrivacySettings): 직렬화할 PrivacySettings 인스턴스.

        Returns:
            dict: 직렬화된 privacy_settings 데이터.
        """
        return {"privacy_settings": instance.privacy_settings}

    def update(self, instance, validated_data):
        """PrivacySettings 인스턴스를 업데이트합니다.

        Args:
            instance (PrivacySettings): 업데이트할 PrivacySettings 인스턴스.
            validated_data (dict): 검증된 업데이트 데이터.

        Returns:
            PrivacySettings: 업데이트된 PrivacySettings 인스턴스.
        """
        privacy_settings = validated_data.get("privacy_settings", {})

        for field, audiences in privacy_settings.items():
            for audience, is_visible in audiences.items():
                instance.set_visibility(field, audience, is_visible)

        instance.save()
        return instance

    def get_visible_fields(self, viewer_type):
        """특정 뷰어 유형에 대해 가시적인 필드 목록을 반환합니다.

        Args:
            viewer_type (str): 뷰어의 유형 (예: 'followers', 'following', 'others').

        Returns:
            list: 가시적인 필드 이름 목록.

        Raises:
            serializers.ValidationError: 잘못된 뷰어 유형인 경우 발생.
        """
        if viewer_type not in [choice[0] for choice in PrivacySettings.PRIVACY_CHOICES]:
            raise serializers.ValidationError("잘못된 뷰어 유형입니다.")

        visible_fields = []
        for field in PrivacySettings.VISIBILITY_FIELDS:
            if self.instance.get_visibility(field, viewer_type):
                visible_fields.append(field)

        return visible_fields
