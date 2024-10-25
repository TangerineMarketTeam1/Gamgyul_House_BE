import uuid
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from follow.models import Follow  # Follow 모델 import 추가

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user1():
    return User.objects.create_user(
        id=uuid.uuid4(),
        username="user1",
        email="user1@test.com",
        password="testpass123",
    )


@pytest.fixture
def user2():
    return User.objects.create_user(
        id=uuid.uuid4(),
        username="user2",
        email="user2@test.com",
        password="testpass123",
    )


@pytest.fixture
def user3():
    return User.objects.create_user(
        id=uuid.uuid4(),
        username="user3",
        email="user3@test.com",
        password="testpass123",
    )


@pytest.fixture
def authenticated_client(api_client, user1):
    api_client.force_authenticate(user=user1)
    return api_client


@pytest.mark.django_db
class TestFollowSystem:
    def test_follow_user(self, authenticated_client, user1, user2):  # user1 추가
        url = reverse("follow", kwargs={"pk": user2.id})
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_201_CREATED
        assert Follow.objects.filter(follower=user1, following=user2).exists()

    def test_follow_self(self, authenticated_client, user1):
        url = reverse("follow", kwargs={"pk": user1.id})
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not Follow.objects.filter(follower=user1, following=user1).exists()

    def test_follow_nonexistent_user(self, authenticated_client):
        non_existent_uuid = uuid.uuid4()
        url = reverse("follow", kwargs={"pk": non_existent_uuid})
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unfollow_user(self, authenticated_client, user1, user2):
        Follow.objects.create(follower=user1, following=user2)
        url = reverse("unfollow", kwargs={"pk": user2.id})
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert not Follow.objects.filter(follower=user1, following=user2).exists()

    def test_unfollow_not_followed_user(
        self, authenticated_client, user1, user2
    ):  # user1 추가
        url = reverse("unfollow", kwargs={"pk": user2.id})
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_follower_list(self, authenticated_client, user1, user2, user3):
        Follow.objects.create(follower=user2, following=user1)
        Follow.objects.create(follower=user3, following=user1)
        url = reverse("follower-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_following_list(self, authenticated_client, user1, user2, user3):
        Follow.objects.create(follower=user1, following=user2)
        Follow.objects.create(follower=user1, following=user3)
        url = reverse("following-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_unauthenticated_access(self, api_client, user2):
        # Follow attempt
        url = reverse("follow", kwargs={"pk": user2.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Unfollow attempt
        url = reverse("unfollow", kwargs={"pk": user2.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Follower list attempt
        url = reverse("follower-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Following list attempt
        url = reverse("following-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_follow_invalid_uuid(self, authenticated_client):
        url = "/follow/follow/invalid-uuid/"
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unfollow_invalid_uuid(self, authenticated_client):
        url = "/follow/unfollow/invalid-uuid/"
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
