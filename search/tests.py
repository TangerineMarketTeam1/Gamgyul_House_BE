from django.urls import reverse
from rest_framework.test import APITransactionTestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class ProfileSearchViewTestCase(APITransactionTestCase):
    def setUp(self):
        User.objects.all().delete()
        self.user1 = User.objects.create_user(
            username="testuser1",
            password="12345",
            email="test1@example.com",
        )
        self.user2 = User.objects.create_user(
            username="testuser2",
            password="12345",
            email="test2@example.com",
        )
        self.user3 = User.objects.create_user(
            username="otheruser",
            password="12345",
            email="other@example.com",
        )
        self.client.force_authenticate(user=self.user1)

    def test_profile_search(self):
        """
        프로필 검색 테스트
        한 명의 사용자가 검색되어야 함(본인 제외)
        """
        url = reverse("profile_search")
        response = self.client.get(url, {"q": "testuser"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(f"Response data: {response.data}")
        self.assertEqual(response.data["count"], 1)

    def test_profile_search_no_query(self):
        """쿼리가 없는 경우 빈 결과 반환 테스트"""
        url = reverse("profile_search")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(f"Response data: {response.data}")
        self.assertEqual(response.data["count"], 0)

    def test_profile_search_no_results(self):
        """쿼리에 일치하는 사용자가 없는 경우 빈 결과 반환 테스트"""
        url = reverse("profile_search")
        response = self.client.get(url, {"q": "nonexistent"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(f"Response data: {response.data}")
        self.assertEqual(response.data["count"], 0)

    def tearDown(self):
        User.objects.all().delete()
        print(f"User count after tearDown: {User.objects.count()}")
