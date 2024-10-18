from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Report
from posts.models import Post
import uuid

User = get_user_model()


class ReportCreateViewTestCase(APITestCase):
    """
    신고 Create API 테스트
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123", username="testuser"
        )
        self.post = Post.objects.create(user=self.user, content="Test post")
        self.url = reverse("report-create")
        self.valid_payload = {
            "content_type": "posts.post",
            "object_id": str(self.post.id),
            "reason": "spam",
            "description": "신고 기능 테스트",
        }

    def test_create_report_authenticated(self):
        """인증된 사용자의 유효한 신고 생성"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.first()
        self.assertEqual(report.reporter, self.user)
        self.assertEqual(report.content_type, ContentType.objects.get_for_model(Post))
        self.assertEqual(report.object_id, str(self.post.id))

    def test_create_report_unauthenticated(self):
        """인증되지 않은 사용자의 신고 시도"""
        response = self.client.post(self.url, self.valid_payload)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )
        self.assertEqual(Report.objects.count(), 0)

    def test_create_report_invalid_content_type(self):
        """잘못된 content_type으로 신고 시도"""
        self.client.force_authenticate(user=self.user)
        invalid_payload = self.valid_payload.copy()
        invalid_payload["content_type"] = "invalid.model"  # 존재하지 않는 app_label
        response = self.client.post(self.url, invalid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Report.objects.count(), 0)

    def test_create_report_invalid_object_id(self):
        """존재하지 않는 object_id로 신고 시도"""
        self.client.force_authenticate(user=self.user)
        invalid_payload = self.valid_payload.copy()
        invalid_payload["object_id"] = str(uuid.uuid4())  # 존재하지 않는 ID
        response = self.client.post(self.url, invalid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Report.objects.count(), 0)

    def test_create_report_invalid_reason(self):
        """잘못된 reason으로 신고 시도"""
        self.client.force_authenticate(user=self.user)
        invalid_payload = self.valid_payload.copy()
        invalid_payload["reason"] = "invalid_reason"
        response = self.client.post(self.url, invalid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Report.objects.count(), 0)

    def test_create_report_missing_required_field(self):
        """필수 필드 누락 시 신고 시도"""
        self.client.force_authenticate(user=self.user)
        invalid_payload = self.valid_payload.copy()
        del invalid_payload["reason"]
        response = self.client.post(self.url, invalid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Report.objects.count(), 0)
