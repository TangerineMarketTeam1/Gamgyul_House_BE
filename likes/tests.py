import uuid
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from follow.models import Follow
from posts.models import Post
from .models import Like

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        username=f"testuser_{uuid.uuid4()}",
        password="testpass",
        email="testuser@example.com",
    )


@pytest.fixture
def popular_users():
    popular_user_1 = User.objects.create_user(
        username=f"popular_user_1_{uuid.uuid4()}",
        password="testpass",
        email="popular_user_1@example.com",
    )
    popular_user_2 = User.objects.create_user(
        username=f"popular_user_2_{uuid.uuid4()}",
        password="testpass",
        email="popular_user_2@example.com",
    )
    return {"user1": popular_user_1, "user2": popular_user_2}


@pytest.fixture
def followed_user():
    return User.objects.create_user(
        username=f"followed_user_{uuid.uuid4()}",
        password="testpass",
        email="followed_user@example.com",
    )


@pytest.fixture
def base_setup(user, popular_users, followed_user):
    # 팔로우 관계 생성
    Follow.objects.create(follower=user, following=followed_user)
    Follow.objects.create(follower=user, following=popular_users["user1"])
    Follow.objects.create(follower=user, following=popular_users["user2"])

    # 인기 사용자 게시글 생성
    Post.objects.create(content="Popular post 1", user=popular_users["user1"])
    Post.objects.create(content="Popular post 2", user=popular_users["user2"])

    # 팔로우한 사용자의 게시글 생성
    followed_post = Post.objects.create(content="Followed post", user=user)

    return {
        "user": user,
        "popular_users": popular_users,
        "followed_user": followed_user,
        "followed_post": followed_post,
    }


@pytest.fixture
def like_setup(base_setup, followed_user):
    # 게시글 생성
    like_post = Post.objects.create(content="Test post", user=followed_user)

    # 인기 사용자 게시글 생성
    popular_post_1 = Post.objects.create(
        content="Popular post 1", user=base_setup["popular_users"]["user1"]
    )
    popular_post_2 = Post.objects.create(
        content="Popular post 2", user=base_setup["popular_users"]["user2"]
    )

    # 팔로우한 사용자의 게시글
    followed_post = Post.objects.create(content="Followed post", user=followed_user)

    return {
        "like_post": like_post,
        "popular_post_1": popular_post_1,
        "popular_post_2": popular_post_2,
        "followed_post": followed_post,
    }


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestPostAPI:
    def test_post_setup(self, base_setup):
        """기본 설정이 제대로 되었는지 확인하는 테스트"""
        popular_posts = Post.objects.filter(
            user__in=[
                base_setup["popular_users"]["user1"],
                base_setup["popular_users"]["user2"],
            ]
        )
        assert popular_posts.count() == 2


@pytest.mark.django_db
class TestLikeAPI:
    def test_like_post(self, authenticated_client, like_setup):
        """게시글 좋아요 테스트"""
        url = reverse("post_like", kwargs={"post_id": str(like_setup["like_post"].id)})
        response = authenticated_client.post(url)

        assert (
            response.status_code == status.HTTP_201_CREATED
        ), f"Expected status code 201, but got {response.status_code}"

        like_setup["like_post"].refresh_from_db()
        assert (
            like_setup["like_post"].likes.count() == 1
        ), f"Expected 1 like, but got {like_setup['like_post'].likes.count()}"

    def test_unlike_post(self, authenticated_client, user, like_setup):
        """게시글 좋아요 취소 테스트"""
        # 먼저 좋아요를 생성
        Like.objects.create(user=user, post=like_setup["like_post"])

        url = reverse("post_like", kwargs={"post_id": str(like_setup["like_post"].id)})
        response = authenticated_client.post(url)

        assert (
            response.status_code == status.HTTP_204_NO_CONTENT
        ), f"Expected status code 204, but got {response.status_code}"

        like_setup["like_post"].refresh_from_db()
        assert (
            like_setup["like_post"].likes.count() == 0
        ), f"Expected 0 likes, but got {like_setup['like_post'].likes.count()}"
