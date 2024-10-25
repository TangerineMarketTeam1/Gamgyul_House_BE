import uuid
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user1():
    return User.objects.create_user(
        username="testuser1", email="testuser1@example.com", password="testpass123"
    )


@pytest.fixture
def user2():
    return User.objects.create_user(
        username="testuser2", email="testuser2@example.com", password="testpass123"
    )


@pytest.fixture
def authenticated_client(api_client, user1):
    api_client.force_authenticate(user=user1)
    return api_client


@pytest.mark.django_db
class TestProfileSystem:
    def test_profile_detail_view(self, authenticated_client, user2):
        url = reverse("profile_detail", kwargs={"id": str(user2.id)})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == "testuser2"

    def test_profile_update_view(self, authenticated_client):
        url = reverse("profile_update")
        data = {"bio": "New bio", "username": "newusername"}
        response = authenticated_client.put(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["bio"] == "New bio"
        assert response.data["username"] == "newusername"

    def test_profile_partial_update_view(self, authenticated_client):
        url = reverse("profile_update")
        data = {"bio": "Updated bio"}
        response = authenticated_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["bio"] == "Updated bio"

    def test_privacy_settings_view_get(self, authenticated_client, user1):
        url = reverse("privacy_settings", kwargs={"user_id": str(user1.id)})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_privacy_settings_view_update(self, authenticated_client, user1):
        url = reverse("privacy_settings", kwargs={"user_id": str(user1.id)})
        data = {
            "privacy_settings": {
                "email": {"followers": True, "following": True, "others": False}
            }
        }
        response = authenticated_client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["privacy_settings"]["email"]["followers"] is True

    def test_privacy_settings_view_partial_update(self, authenticated_client, user1):
        url = reverse("privacy_settings", kwargs={"user_id": str(user1.id)})
        data = {"privacy_settings": {"email": {"others": True}}}
        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["privacy_settings"]["email"]["others"] is True

    def test_unauthorized_access(self, api_client, user2):
        url = reverse("profile_detail", kwargs={"id": str(user2.id)})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_privacy_settings_permission_denied(self, authenticated_client, user2):
        url = reverse("privacy_settings", kwargs={"user_id": str(user2.id)})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_profile_not_found(self, authenticated_client):
        url = reverse("profile_detail", kwargs={"id": str(uuid.uuid4())})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
