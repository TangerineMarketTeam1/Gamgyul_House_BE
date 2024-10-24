import pytest
from itertools import count
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from posts.models import Post
from taggit.models import Tag

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpassword123",
    )


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def user_counter():
    return count(1)


@pytest.fixture
def create_user(user_counter):
    def _create_user(username=None):
        counter = next(user_counter)
        if username is None:
            username = f"testuser{counter}"
        return User.objects.create_user(
            username=username,
            password="testpass123",
            email=f"{username}@example.com",
        )

    return _create_user


@pytest.fixture
def create_post():
    def _create_post(user, tags):
        post = Post.objects.create(user=user, content="Test post")
        post.tags.add(*tags)
        return post

    return _create_post


@pytest.mark.django_db
class TestFriendRecommendation:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.url = reverse("friend_recommendation")

    def test_common_followers_recommendation(
        self, authenticated_client, user, create_user
    ):
        """팔로워 기반 추천 테스트"""
        follower1 = create_user("follower1")
        follower2 = create_user("follower2")
        common_friend = create_user("common_friend")

        user.followers.create(follower=follower1)
        user.followers.create(follower=follower2)
        follower1.followers.create(follower=common_friend)
        follower2.followers.create(follower=common_friend)

        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        assert any(r["username"] == "common_friend" for r in response.data)

    def test_common_interests_recommendation(
        self, authenticated_client, user, create_user, create_post
    ):
        """태그 기반 추천 테스트"""
        other_user = create_user("otheruser")

        tag = Tag.objects.create(name="common_interest")
        create_post(user, [tag])
        create_post(other_user, [tag])

        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        assert any(r["username"] == "otheruser" for r in response.data)

    def test_popular_users_recommendation(self, authenticated_client, create_user):
        """인기 사용자 추천 테스트"""
        popular_user = create_user("popularuser")

        # 인기 사용자를 만들기 위해 팔로워 5명으로 추가
        for i in range(5):
            follower = create_user(f"follower{i}")
            popular_user.followers.create(follower=follower)

        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        assert any(r["username"] == "popularuser" for r in response.data)

    def test_max_recommendations(self, authenticated_client, create_user):
        """최대 15명까지만 추천 받도록 제한 테스트"""
        for i in range(20):
            create_user(f"user{i}")

        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        print(f"Response data: {response.data}")
        assert len(response.data) <= 15

    def test_authenticated_user_required(self, api_client):
        """인증된 사용자 테스트"""
        response = api_client.get(self.url)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]
