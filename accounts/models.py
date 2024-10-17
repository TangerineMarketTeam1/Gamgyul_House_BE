import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField("이메일 주소", unique=True)
    username = models.CharField(
        "사용자명",
        max_length=150,
        unique=True,
        help_text="필수 항목입니다. 150자 이하로 작성해주세요. 문자, 숫자 그리고 @/./+/-/_만 사용 가능합니다.",
        validators=[AbstractUser.username_validator],
        error_messages={
            "unique": "이미 사용 중인 사용자명입니다.",
        },
    )
    profile_image = models.ImageField(
        upload_to="profile_images/", null=True, blank=True
    )
    bio = models.TextField(max_length=500, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.username
