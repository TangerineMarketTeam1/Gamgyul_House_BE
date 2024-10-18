from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class ProfileViewsTestCase(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="testuser1", email="testuser1@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="testuser2", email="testuser2@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user1)

    def test_profile_detail_view(self):
        url = reverse("profile-detail", kwargs={"id": str(self.user2.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "testuser2")

    def test_profile_update_view(self):
        url = reverse("profile-update")
        data = {"bio": "New bio", "username": "newusername"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["bio"], "New bio")
        self.assertEqual(response.data["username"], "newusername")

    def test_profile_partial_update_view(self):
        url = reverse("profile-update")
        data = {"bio": "Updated bio"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["bio"], "Updated bio")

    def test_privacy_settings_view_get(self):
        url = reverse("privacy-settings", kwargs={"user_id": str(self.user1.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_privacy_settings_view_update(self):
        url = reverse("privacy-settings", kwargs={"user_id": str(self.user1.id)})
        data = {
            "privacy_settings": {
                "email": {"followers": True, "following": True, "others": False}
            }
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["data"]["privacy_settings"]["email"]["followers"], True
        )

    def test_privacy_settings_view_partial_update(self):
        url = reverse("privacy-settings", kwargs={"user_id": str(self.user1.id)})
        data = {"privacy_settings": {"email": {"others": True}}}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["data"]["privacy_settings"]["email"]["others"], True
        )

    def test_unauthorized_access(self):
        self.client.force_authenticate(user=None)
        url = reverse("profile-detail", kwargs={"id": str(self.user2.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_privacy_settings_permission_denied(self):
        url = reverse("privacy-settings", kwargs={"user_id": str(self.user2.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_profile_not_found(self):
        url = reverse("profile-detail", kwargs={"id": str(uuid.uuid4())})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
