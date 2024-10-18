from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from posts.models import Post
from taggit.models import Tag
from itertools import count

User = get_user_model()


class FriendRecommendationViewTestCase(APITestCase):
    """
    친구 추천 테스트
    """

    def setUp(self):
        """기본 세팅"""
        self.url = reverse("friend_recommendation")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
        )
        self.client.force_authenticate(user=self.user)
        self.user_counter = count(1)

    def create_user(self, username=None):
        counter = next(self.user_counter)
        if username is None:
            username = f"testuser{counter}"
        return User.objects.create_user(
            username=username,
            password="testpass123",
            email=f"{username}@example.com",
        )

    def create_post(self, user, tags):
        post = Post.objects.create(user=user, content="Test post")
        post.tags.add(*tags)
        return post

    def test_common_followers_recommendation(self):
        """팔로워 기반 추천 테스트"""
        follower1 = self.create_user("follower1")
        follower2 = self.create_user("follower2")
        common_friend = self.create_user("common_friend")

        self.user.followers.create(follower=follower1)
        self.user.followers.create(follower=follower2)
        follower1.followers.create(follower=common_friend)
        follower2.followers.create(follower=common_friend)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        self.assertTrue(any(r["username"] == "common_friend" for r in response.data))

    def test_common_interests_recommendation(self):
        """태그 기반 추천 테스트"""
        other_user = self.create_user("otheruser")

        tag = Tag.objects.create(name="common_interest")
        self.create_post(self.user, [tag])
        self.create_post(other_user, [tag])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        self.assertTrue(any(r["username"] == "otheruser" for r in response.data))

    def test_popular_users_recommendation(self):
        """
        인기 사용자 추천 테스트
        인기 사용자를 만들기 위해 팔로워 5명으로 추가
        """
        popular_user = self.create_user("popularuser")

        for i in range(5):
            follower = self.create_user(f"follower{i}")
            popular_user.followers.create(follower=follower)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        self.assertTrue(any(r["username"] == "popularuser" for r in response.data))

    def test_max_recommendations(self):
        """
        최대 15명까지만 추천 받도록 제한 테스트
        """
        for i in range(20):
            self.create_user(f"user{i}")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(f"Response data: {response.data}")
        self.assertTrue(len(response.data) <= 15)

    def test_authenticated_user_required(self):
        """인증된 사용자 테스트"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )
