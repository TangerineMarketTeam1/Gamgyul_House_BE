from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import json

User = get_user_model()


class PrivacySettings(models.Model):
    """
    프로필 공개 설정을 관리하는 모델.

    이 모델은 사용자의 프로필 정보에 대한 공개 설정을 저장하고 관리합니다.
    각 정보 필드(이메일, 바이오 등)에 대해 팔로워, 팔로잉, 기타 사용자별로
    공개 여부를 설정할 수 있습니다.

    Attributes:
        user (OneToOneField): 연결된 User 모델 인스턴스.
        privacy_settings (JSONField): 개인정보 설정을 저장하는 JSON 필드.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="privacy_settings"
    )

    PRIVACY_CHOICES = [
        ("followers", "Followers"),
        ("following", "Following"),
        ("others", "Others"),
    ]

    VISIBILITY_FIELDS = [
        "email",
        "bio",
        "posts",
        "following_list",
        "follower_list",
    ]

    privacy_settings = models.JSONField(default=dict)

    def set_visibility(self, field, audience, is_visible):
        """
        특정 필드와 대상에 대한 공개 설정을 변경합니다.

        Args:
            field (str): 설정을 변경할 필드 이름.
            audience (str): 설정을 변경할 대상 그룹.
            is_visible (bool): 공개 여부.

        Raises:
            ValidationError: 유효하지 않은 필드나 대상이 제공된 경우.
        """
        if field not in self.VISIBILITY_FIELDS:
            raise ValidationError(f"Invalid field: {field}")
        if audience not in [choice[0] for choice in self.PRIVACY_CHOICES]:
            raise ValidationError(f"Invalid audience: {audience}")

        if not self.privacy_settings:
            self.privacy_settings = {}

        if field not in self.privacy_settings:
            self.privacy_settings[field] = {}

        self.privacy_settings[field][audience] = is_visible
        self.save()

    def get_visibility(self, field, audience):
        """
        특정 필드와 대상에 대한 현재 공개 설정을 반환합니다.

        Args:
            field (str): 확인할 필드 이름.
            audience (str): 확인할 대상 그룹.

        Returns:
            bool: 해당 필드와 대상에 대한 공개 여부.

        Raises:
            ValidationError: 유효하지 않은 필드나 대상이 제공된 경우.
        """
        if field not in self.VISIBILITY_FIELDS:
            raise ValidationError(f"Invalid field: {field}")
        if audience not in [choice[0] for choice in self.PRIVACY_CHOICES]:
            raise ValidationError(f"Invalid audience: {audience}")

        return self.privacy_settings.get(field, {}).get(audience, False)

    def __str__(self):
        """PrivacySettings 인스턴스의 문자열 표현을 반환합니다."""
        return f"{self.user.username}'s Privacy Settings"

    def save(self, *args, **kwargs):
        """모델 인스턴스를 저장하기 전에 기본 privacy_settings를 설정합니다."""
        if not self.privacy_settings:
            self.privacy_settings = {
                field: {audience: False for audience, _ in self.PRIVACY_CHOICES}
                for field in self.VISIBILITY_FIELDS
            }
        super().save(*args, **kwargs)
