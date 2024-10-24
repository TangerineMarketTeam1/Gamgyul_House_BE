import uuid
from django.db import models
from django.contrib.auth import get_user_model
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFit

User = get_user_model()


class UUIDTaggedItem(TaggedItemBase):
    """UUID 기반의 커스텀 TaggedItem 모델"""

    content_object = models.ForeignKey("Post", on_delete=models.CASCADE)
    object_id = models.UUIDField(default=uuid.uuid4, db_index=True)


class Post(models.Model):
    """게시물 모델"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=False, null=False)
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = TaggableManager(through=UUIDTaggedItem, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"


class PostImage(models.Model):
    """게시물 이미지 모델"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")
    image = ProcessedImageField(
        upload_to="posts/%Y/%m/%d/",
        processors=[ResizeToFit(1920, 1080)],
        format="JPEG",
        options={"quality": 90},
    )

    class Meta:
        ordering = ["post"]

    def __str__(self):
        return f"Image for {self.post.user.username}"
