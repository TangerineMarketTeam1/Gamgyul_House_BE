import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Product, ProductImage
from datetime import date
from decimal import Decimal
import json

User = get_user_model()


class ProductTests(APITestCase):
    """Product 관련 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client = APIClient()

        # 테스트용 이미지 파일 생성
        self.image_content = b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
        self.image = SimpleUploadedFile(
            "test_image.gif", self.image_content, content_type="image/gif"
        )

        # 기본 상품 데이터
        self.product_data = {
            "name": "테스트 상품",
            "price": "10000.00",
            "description": "테스트 상품 설명",
            "stock": 100,
            "variety": "테스트 품종",
            "growing_region": "테스트 지역",
            "harvest_date": "2024-01-01",
        }

    def get_tokens_for_user(self, user):
        """사용자의 JWT 토큰을 반환"""
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    def test_create_product(self):
        """상품 생성 테스트"""
        self.client.force_authenticate(user=self.user)

        self.product_data["images"] = [self.image]
        response = self.client.post(
            reverse("product-list"), self.product_data, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(ProductImage.objects.count(), 1)
        self.assertEqual(response.data["name"], "테스트 상품")

    def test_get_product_list(self):
        """상품 목록 조회 테스트"""
        product = Product.objects.create(user=self.user, **self.product_data)

        response = self.client.get(reverse("product-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data["results"]), 0)

    def test_get_product_detail(self):
        """상품 상세 조회 테스트"""
        product = Product.objects.create(user=self.user, **self.product_data)

        response = self.client.get(reverse("product-detail", kwargs={"id": product.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.product_data["name"])

    def test_update_product(self):
        """상품 수정 테스트"""
        self.client.force_authenticate(user=self.user)
        product = Product.objects.create(user=self.user, **self.product_data)

        updated_data = {
            "name": "수정된 상품",
            "price": "20000.00",
        }

        response = self.client.patch(
            reverse("product-detail", kwargs={"id": product.id}),
            updated_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "수정된 상품")
        self.assertEqual(response.data["price"], "20000.00")

    def test_delete_product(self):
        """상품 삭제 테스트"""
        self.client.force_authenticate(user=self.user)
        product = Product.objects.create(user=self.user, **self.product_data)

        response = self.client.delete(
            reverse("product-detail", kwargs={"id": product.id})
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 0)

    def test_unauthorized_access(self):
        """인증되지 않은 사용자 접근 테스트"""
        response = self.client.post(
            reverse("product-list"), self.product_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_product_image_limit(self):
        """이미지 업로드 제한 테스트"""
        self.client.force_authenticate(user=self.user)

        images = [
            SimpleUploadedFile(
                f"test_image_{i}.gif", self.image_content, content_type="image/gif"
            )
            for i in range(6)
        ]

        self.product_data["images"] = images
        response = self.client.post(
            reverse("product-list"), self.product_data, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "최대 5장까지만 이미지를 업로드할 수 있습니다", str(response.data)
        )

    def test_search_product_with_filters(self):
        """상품 필터 검색 테스트"""
        Product.objects.create(user=self.user, **self.product_data)

        # 품종으로 검색
        response = self.client.get(f"{reverse('product-list')}?variety=테스트 품종")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data["results"]), 0)

        # 재배 지역으로 검색
        response = self.client.get(
            f"{reverse('product-list')}?growing_region=테스트 지역"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data["results"]), 0)

    def test_other_user_update_product(self):
        """다른 사용자의 상품 수정 시도 테스트"""
        # 상품 생성
        product = Product.objects.create(user=self.user, **self.product_data)

        # 다른 사용자 생성
        other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="otherpass123"
        )

        # 다른 사용자로 인증
        self.client.force_authenticate(user=other_user)

        updated_data = {
            "name": "수정된 상품",
            "price": "20000.00",
        }

        response = self.client.patch(
            reverse("product-detail", kwargs={"id": product.id}),
            updated_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
