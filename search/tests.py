import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from market.models import Product

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


@pytest.mark.django_db(transaction=True)
class TestProductSearch:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.url = reverse("product_search")

    @pytest.fixture
    def products(self, users):
        """테스트용 상품 데이터 생성"""
        products = [
            Product.objects.create(
                name="유기농 사과",
                stock=100,
                price=35000,  # price 필드 추가
                user=users["user1"],
            ),
            Product.objects.create(
                name="청송 꿀사과",
                stock=50,
                price=45000,  # price 필드 추가
                user=users["user2"],
            ),
            Product.objects.create(
                name="제주 감귤",
                stock=200,
                price=25000,  # price 필드 추가
                user=users["user3"],
            ),
        ]
        return products

    def test_product_search_by_name(self, authenticated_client, products):
        """상품명으로 검색 테스트"""
        response = authenticated_client.get(self.url, {"q": "사과", "category": "name"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2
        assert all("사과" in product["name"] for product in response.data["results"])

    def test_product_search_by_user(self, authenticated_client, products, users):
        """판매자로 검색 테스트"""
        response = authenticated_client.get(
            self.url, {"q": users["user2"].username, "category": "user"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["user"] == users["user2"].username

    def test_product_search_no_query(self, authenticated_client, products):
        """검색어 없는 경우 테스트"""
        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_product_search_no_results(self, authenticated_client, products):
        """검색 결과 없는 경우 테스트"""
        response = authenticated_client.get(self.url, {"q": "존재하지않는상품"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_product_search_all_fields(self, authenticated_client, products):
        """전체 필드 검색 테스트"""
        response = authenticated_client.get(self.url, {"q": "사과"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2
        assert any("사과" in product["name"] for product in response.data["results"])
