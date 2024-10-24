import uuid
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
from rest_framework import status
from reports.models import Report
from posts.models import Post

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        email="test@example.com", password="testpass123", username="testuser"
    )


@pytest.fixture
def post(user):
    return Post.objects.create(user=user, content="Test post")


@pytest.fixture
def valid_payload(post):
    return {
        "content_type": "posts.post",
        "object_id": str(post.id),
        "reason": "spam",
        "description": "신고 기능 테스트",
    }


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestReportCreate:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.url = reverse("report-create")

    def test_create_report_authenticated(
        self, authenticated_client, user, post, valid_payload
    ):
        """인증된 사용자의 유효한 신고 생성"""
        response = authenticated_client.post(self.url, valid_payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert Report.objects.count() == 1

        report = Report.objects.first()
        assert report.reporter == user
        assert report.content_type == ContentType.objects.get_for_model(Post)
        assert report.object_id == str(post.id)

    def test_create_report_unauthenticated(self, api_client, valid_payload):
        """인증되지 않은 사용자의 신고 시도"""
        response = api_client.post(self.url, valid_payload)

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]
        assert Report.objects.count() == 0

    def test_create_report_invalid_content_type(
        self, authenticated_client, valid_payload
    ):
        """잘못된 content_type으로 신고 시도"""
        invalid_payload = valid_payload.copy()
        invalid_payload["content_type"] = "invalid.model"  # 존재하지 않는 app_label

        response = authenticated_client.post(self.url, invalid_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Report.objects.count() == 0

    def test_create_report_invalid_object_id(self, authenticated_client, valid_payload):
        """존재하지 않는 object_id로 신고 시도"""
        invalid_payload = valid_payload.copy()
        invalid_payload["object_id"] = str(uuid.uuid4())  # 존재하지 않는 ID

        response = authenticated_client.post(self.url, invalid_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Report.objects.count() == 0

    def test_create_report_invalid_reason(self, authenticated_client, valid_payload):
        """잘못된 reason으로 신고 시도"""
        invalid_payload = valid_payload.copy()
        invalid_payload["reason"] = "invalid_reason"

        response = authenticated_client.post(self.url, invalid_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Report.objects.count() == 0

    def test_create_report_missing_required_field(
        self, authenticated_client, valid_payload
    ):
        """필수 필드 누락 시 신고 시도"""
        invalid_payload = valid_payload.copy()
        del invalid_payload["reason"]

        response = authenticated_client.post(self.url, invalid_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Report.objects.count() == 0
