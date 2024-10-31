import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Product, ProductImage
import json

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_user():
    return User.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123"
    )


@pytest.fixture
def test_image():
    image_content = b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    return SimpleUploadedFile("test_image.gif", image_content, content_type="image/gif")


@pytest.fixture
def product_data():
    return {
        "name": "테스트 상품",
        "price": "10000.00",
        "description": "테스트 상품 설명",
        "stock": 100,
        "variety": "테스트 품종",
        "growing_region": "테스트 지역",
        "harvest_date": "2024-01-01",
    }


@pytest.fixture
def authenticated_client(api_client, test_user):
    api_client.force_authenticate(user=test_user)
    return api_client


@pytest.mark.django_db
def test_create_product(authenticated_client, product_data, test_image):
    """상품 생성 테스트"""
    product_data["images"] = [test_image]
    response = authenticated_client.post(
        reverse("product-list"), product_data, format="multipart"
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert Product.objects.count() == 1
    assert ProductImage.objects.count() == 1
    assert response.data["name"] == "테스트 상품"


@pytest.mark.django_db
def test_get_product_list(api_client, test_user, product_data):
    """상품 목록 조회 테스트"""
    Product.objects.create(user=test_user, **product_data)
    response = api_client.get(reverse("product-list"))

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) > 0


@pytest.mark.django_db
def test_get_product_detail(api_client, test_user, product_data):
    """상품 상세 조회 테스트"""
    product = Product.objects.create(user=test_user, **product_data)
    response = api_client.get(reverse("product-detail", kwargs={"id": product.id}))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == product_data["name"]


@pytest.mark.django_db
def test_update_product(authenticated_client, test_user, product_data, test_image):
    """상품 수정 테스트"""
    product = Product.objects.create(user=test_user, **product_data)
    initial_image = ProductImage.objects.create(product=product, image=test_image)

    new_test_image = SimpleUploadedFile(
        "new_test_image.gif",
        b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
        content_type="image/gif",
    )

    updated_data = {
        "name": "수정된 상품",
        "price": "20000.00",
        "images_to_delete": [initial_image.image.url],
        "image": [new_test_image],
    }

    response = authenticated_client.patch(
        reverse("product-detail", kwargs={"id": product.id}),
        updated_data,
        format="multipart",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == "수정된 상품"
    assert response.data["price"] == "20000.00"

    product.refresh_from_db()
    assert product.images.count() == 1
    assert not ProductImage.objects.filter(id=initial_image.id).exists()

    assert product.images.exists()


@pytest.mark.django_db
def test_delete_product(authenticated_client, test_user, product_data):
    """상품 삭제 테스트"""
    product = Product.objects.create(user=test_user, **product_data)
    response = authenticated_client.delete(
        reverse("product-detail", kwargs={"id": product.id})
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Product.objects.count() == 0


@pytest.mark.django_db
def test_unauthorized_access(api_client, product_data):
    """인증되지 않은 사용자 접근 테스트"""
    response = api_client.post(reverse("product-list"), product_data, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_product_image_limit(authenticated_client, product_data, test_image):
    """이미지 업로드 제한 테스트"""
    images = [
        SimpleUploadedFile(
            f"test_image_{i}.gif", test_image.read(), content_type="image/gif"
        )
        for i in range(6)
    ]
    test_image.seek(0)  # Reset file pointer

    product_data["images"] = images
    response = authenticated_client.post(
        reverse("product-list"), product_data, format="multipart"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "최대 5장까지만 이미지를 업로드할 수 있습니다" in str(response.data)


@pytest.mark.django_db
def test_search_product_with_filters(api_client, test_user, product_data):
    """상품 필터 검색 테스트"""
    Product.objects.create(user=test_user, **product_data)

    # 품종으로 검색
    response = api_client.get(f"{reverse('product-list')}?variety=테스트 품종")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) > 0

    # 재배 지역으로 검색
    response = api_client.get(f"{reverse('product-list')}?growing_region=테스트 지역")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) > 0


@pytest.mark.django_db
def test_other_user_update_product(api_client, test_user, product_data):
    """다른 사용자의 상품 수정 시도 테스트"""
    product = Product.objects.create(user=test_user, **product_data)

    other_user = User.objects.create_user(
        username="otheruser", email="other@example.com", password="otherpass123"
    )
    api_client.force_authenticate(user=other_user)

    updated_data = {
        "name": "수정된 상품",
        "price": "20000.00",
    }

    response = api_client.patch(
        reverse("product-detail", kwargs={"id": product.id}),
        updated_data,
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
