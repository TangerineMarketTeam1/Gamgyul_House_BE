from django.db import models
from django.contrib.auth import get_user_model
from posts.models import Post

User = get_user_model()


class Like(models.Model):
    """좋아요 모델"""

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} likes {self.post}"
