import uuid
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Follow

User = get_user_model()


class FollowViewsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            id=uuid.uuid4(),
            username="user1",
            email="user1@test.com",
            password="testpass123",
        )
        self.user2 = User.objects.create_user(
            id=uuid.uuid4(),
            username="user2",
            email="user2@test.com",
            password="testpass123",
        )
        self.user3 = User.objects.create_user(
            id=uuid.uuid4(),
            username="user3",
            email="user3@test.com",
            password="testpass123",
        )

    def test_follow_user(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse("follow", kwargs={"pk": self.user2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Follow.objects.filter(follower=self.user1, following=self.user2).exists()
        )

    def test_follow_self(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse("follow", kwargs={"pk": self.user1.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            Follow.objects.filter(follower=self.user1, following=self.user1).exists()
        )

    def test_follow_nonexistent_user(self):
        self.client.force_authenticate(user=self.user1)
        non_existent_uuid = uuid.uuid4()
        url = reverse("follow", kwargs={"pk": non_existent_uuid})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unfollow_user(self):
        Follow.objects.create(follower=self.user1, following=self.user2)
        self.client.force_authenticate(user=self.user1)
        url = reverse("unfollow", kwargs={"pk": self.user2.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            Follow.objects.filter(follower=self.user1, following=self.user2).exists()
        )

    def test_unfollow_not_followed_user(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse("unfollow", kwargs={"pk": self.user2.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_follower_list(self):
        Follow.objects.create(follower=self.user2, following=self.user1)
        Follow.objects.create(follower=self.user3, following=self.user1)
        self.client.force_authenticate(user=self.user1)
        url = reverse("follower-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_following_list(self):
        Follow.objects.create(follower=self.user1, following=self.user2)
        Follow.objects.create(follower=self.user1, following=self.user3)
        self.client.force_authenticate(user=self.user1)
        url = reverse("following-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_unauthenticated_access(self):
        url = reverse("follow", kwargs={"pk": self.user2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        url = reverse("unfollow", kwargs={"pk": self.user2.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        url = reverse("follower-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        url = reverse("following-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_follow_invalid_uuid(self):
        self.client.force_authenticate(user=self.user1)
        url = "/follow/follow/invalid-uuid/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unfollow_invalid_uuid(self):
        self.client.force_authenticate(user=self.user1)
        url = "/follow/unfollow/invalid-uuid/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
