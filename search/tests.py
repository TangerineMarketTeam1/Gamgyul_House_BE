import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(autouse=True)
def clean_users():
    User.objects.all().delete()
    yield
    User.objects.all().delete()
    print(f"User count after cleanup: {User.objects.count()}")


@pytest.fixture
def users():
    user1 = User.objects.create_user(
        username="testuser1",
        password="12345",
        email="test1@example.com",
    )
    user2 = User.objects.create_user(
        username="testuser2",
        password="12345",
        email="test2@example.com",
    )
    user3 = User.objects.create_user(
        username="otheruser",
        password="12345",
        email="other@example.com",
    )
    return {"user1": user1, "user2": user2, "user3": user3}


@pytest.fixture
def authenticated_client(api_client, users):
    api_client.force_authenticate(user=users["user1"])
    return api_client


@pytest.mark.django_db(transaction=True)
class TestProfileSearch:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.url = reverse("profile_search")

    def test_profile_search(self, authenticated_client):
        """
        프로필 검색 테스트
        한 명의 사용자가 검색되어야 함(본인 제외)
        """
        response = authenticated_client.get(self.url, {"q": "testuser"})

        assert response.status_code == status.HTTP_200_OK
        print(f"Response data: {response.data}")
        assert response.data["count"] == 1

    def test_profile_search_no_query(self, authenticated_client):
        """쿼리가 없는 경우 빈 결과 반환 테스트"""
        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        print(f"Response data: {response.data}")
        assert response.data["count"] == 0

    def test_profile_search_no_results(self, authenticated_client):
        """쿼리에 일치하는 사용자가 없는 경우 빈 결과 반환 테스트"""
        response = authenticated_client.get(self.url, {"q": "nonexistent"})

        assert response.status_code == status.HTTP_200_OK
        print(f"Response data: {response.data}")
        assert response.data["count"] == 0
