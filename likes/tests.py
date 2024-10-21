import uuid
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from follow.models import Follow
from posts.models import Post
from .models import Like


User = get_user_model()


class TestPostAPI(APITestCase):
    def setUp(self):
        """테스트를 위한 APIClient 인스턴스 생성"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username=f"testuser_{uuid.uuid4()}",
            password="testpass",
            email="testuser@example.com",
        )

        # 인기 사용자 생성
        self.popular_user_1 = User.objects.create_user(
            username=f"popular_user_1_{uuid.uuid4()}",
            password="testpass",
            email="popular_user_1@example.com",
        )

        self.popular_user_2 = User.objects.create_user(
            username=f"popular_user_2_{uuid.uuid4()}",
            password="testpass",
            email="popular_user_2@example.com",
        )

        # 팔로우한 사용자 생성
        self.followed_user = User.objects.create_user(  # 여기서 정의
            username=f"followed_user_{uuid.uuid4()}",
            password="testpass",
            email="followed_user@example.com",
        )
        Follow.objects.create(follower=self.user, following=self.followed_user)

        # 인기 사용자의 팔로워 생성
        Follow.objects.create(follower=self.user, following=self.popular_user_1)
        Follow.objects.create(follower=self.user, following=self.popular_user_2)

        # 인기 사용자 게시글 생성
        Post.objects.create(content="Popular post 1", user=self.popular_user_1)
        Post.objects.create(content="Popular post 2", user=self.popular_user_2)

        # 생성된 게시물 ID 확인
        popular_posts = Post.objects.filter(
            user__in=[self.popular_user_1, self.popular_user_2]
        )

        # 팔로우한 사용자의 게시글 생성
        self.followed_post = Post.objects.create(
            content="Followed post", user=self.user
        )


class TestLikeAPI(TestPostAPI):
    def setUp(self):
        """테스트를 위한 APIClient 인스턴스 생성"""
        super().setUp()

        # 게시글 생성
        self.like_post = Post.objects.create(
            content="Test post", user=self.followed_user
        )

        # 인기 사용자로부터 게시글 생성
        self.popular_post_1 = Post.objects.create(
            content="Popular post 1", user=self.popular_user_1
        )
        self.popular_post_2 = Post.objects.create(
            content="Popular post 2", user=self.popular_user_2
        )

        # 팔로우한 사용자의 게시글 생성
        self.followed_post = Post.objects.create(
            content="Followed post", user=self.followed_user
        )

    def test_like_post(self):
        """게시글 좋아요 테스트"""
        self.client.force_authenticate(user=self.user)
        url = reverse("post_like", kwargs={"post_id": str(self.like_post.id)})
        response = self.client.post(url)
        assert (
            response.status_code == status.HTTP_201_CREATED
        ), f"Expected status code 201, but got {response.status_code}"
        self.like_post.refresh_from_db()
        assert (
            self.like_post.likes.count() == 1
        ), f"Expected 1 like, but got {self.like_post.likes.count()}"

    def test_unlike_post(self):
        """게시글 좋아요 취소 테스트"""
        # Like 인스턴스를 생성하여 게시글에 추가
        Like.objects.create(user=self.user, post=self.like_post)

        self.client.force_authenticate(user=self.user)
        url = reverse("post_like", kwargs={"post_id": str(self.like_post.id)})
        response = self.client.post(url)

        assert (
            response.status_code == status.HTTP_204_NO_CONTENT
        ), f"Expected status code 204, but got {response.status_code}"
        self.like_post.refresh_from_db()  # 게시글 데이터를 최신 상태로 갱신
        assert (
            self.like_post.likes.count() == 0
        ), f"Expected 0 likes, but got {self.like_post.likes.count()}"
