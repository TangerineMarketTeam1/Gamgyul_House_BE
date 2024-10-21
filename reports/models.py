from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


class Report(models.Model):
    """신고를 저장하는 모델"""

    REPORT_REASONS = [
        ("spam", "스팸"),
        ("abuse", "욕설/비방"),
        ("adult", "성인 콘텐츠"),
        ("other", "기타"),
    ]
    REPORT_STATUS = [
        ("pending", "처리 대기"),
        ("in_progress", "처리 중"),
        ("resolved", "해결됨"),
        ("rejected", "반려됨"),
    ]

    reporter = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reports_submitted"
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)
    reported_content = GenericForeignKey("content_type", "object_id")
    reason = models.CharField(choices=REPORT_REASONS)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(choices=REPORT_STATUS, default="pending")
    admin_comment = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("reporter", "content_type", "object_id")
        permissions = [
            ("can_process_reports", "Can process reports"),
        ]

    def __str__(self):
        return f"Report by {self.reporter.username} on {self.content_type}"
