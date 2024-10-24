import os
import uuid
import pytest
import tempfile
from PIL import Image
from contextlib import contextmanager
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from follow.models import Follow
from .models import Post

User = get_user_model()


@pytest.fixture
def api_client():
    """테스트를 위한 APIClient 인스턴스 생성"""
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
    return popular_user_1, popular_user_2


@pytest.fixture
def followed_user():
    return User.objects.create_user(
        username=f"followed_user_{uuid.uuid4()}",
        password="testpass",
        email="followed_user@example.com",
    )


@pytest.fixture
def create_followers(user, followed_user, popular_users):
    Follow.objects.create(follower=user, following=followed_user)
    Follow.objects.create(follower=user, following=popular_users[0])
    Follow.objects.create(follower=user, following=popular_users[1])


@pytest.fixture
def create_posts(popular_users, user):
    Post.objects.create(content="Popular post 1", user=popular_users[0])
    Post.objects.create(content="Popular post 2", user=popular_users[1])
    Post.objects.create(content="Followed post", user=user)


@pytest.fixture
def create_temp_image():
    """임시 이미지 파일들을 생성하고 관리하는 fixture"""
    temp_files = []

    @contextmanager
    def make_image():
        image = Image.new("RGB", (100, 100))
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            image.save(temp_file.name)
            temp_files.append(temp_file.name)
            yield temp_file.name

    yield make_image

    # fixture가 끝나면 임시 파일들을 모두 삭제
    for temp_file in temp_files:
        try:
            os.remove(temp_file)
        except OSError as e:
            print(f"Error deleting file {temp_file}: {e}")

    # fixture가 끝나면 임시 파일들을 모두 삭제
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError as e:
                print(f"Error deleting file {temp_file}: {e}")


@pytest.mark.django_db
def test_create_post(api_client, user, create_temp_image):
    """게시글 생성 테스트"""
    api_client.force_authenticate(user=user)
    Post.objects.all().delete()

    url = reverse("post-list")

    # create_temp_image를 사용하여 이미지 파일 생성
    with create_temp_image() as image_path:
        with open(image_path, "rb") as image_file:
            data = {
                "content": "This is a test post.",
                "tags": ["testtag1", "testtag2"],
                "images": [image_file],
            }
            response = api_client.post(url, data, format="multipart")

    # 응답 상태 코드 확인
    assert response.status_code == status.HTTP_201_CREATED
    assert Post.objects.count() == 1

    # 테스트 후 포스트 삭제
    post = Post.objects.first()
    post.delete()  # S3에서 이미지 삭제 포함


@pytest.mark.django_db
def test_post_list_authenticated_user_with_followings(api_client, user, followed_user):
    """팔로우한 사용자가 있는 인증된 사용자의 게시글 목록 조회 테스트"""
    Follow.objects.create(follower=user, following=followed_user)

    post = Post.objects.create(
        content="This is a post by followed user.", user=followed_user
    )

    api_client.force_authenticate(user=user)
    response = api_client.get(reverse("post-list"))

    # 응답 코드 및 게시글이 포함되어 있는지 확인
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) > 0
    assert any(item["id"] == str(post.id) for item in response.data["results"])


@pytest.mark.django_db
def test_post_list_authenticated_user_without_followings(
    api_client, user, popular_users
):
    """팔로우한 사용자가 없는 인증된 사용자의 게시글 목록 조회 테스트"""
    # 인기 사용자 게시물 생성
    for popular_user in popular_users:
        Post.objects.create(
            content=f"Post by {popular_user.username}", user=popular_user
        )

    api_client.force_authenticate(user=user)

    popular_posts_count = Post.objects.filter(user__in=popular_users).count()
    assert popular_posts_count > 0, "인기 게시물이 데이터베이스에 존재하지 않습니다."

    # 게시글 목록 조회 요청
    response = api_client.get(reverse("post-list"))

    # 응답 코드 확인
    assert response.status_code == status.HTTP_200_OK

    # 결과가 비어 있지 않은지 확인
    assert len(response.data["results"]) > 0, "결과가 비어 있습니다."

    # 인기 사용자 게시물이 포함되어 있는지 확인
    popular_post_ids = list(
        Post.objects.filter(user__in=popular_users).values_list("id", flat=True)
    )
    response_post_ids = [item["id"] for item in response.data["results"]]

    # UUID를 문자열로 변환하여 비교
    popular_post_ids_str = [str(post_id) for post_id in popular_post_ids]

    # 인기 사용자 게시물이 응답에 포함되어 있는지 확인
    assert any(post_id in response_post_ids for post_id in popular_post_ids_str), (
        f"인기 사용자의 게시물이 응답에 포함되지 않았습니다. "
        f"응답 게시물 ID: {response_post_ids}, 인기 게시물 ID: {popular_post_ids_str}"
    )


@pytest.mark.django_db
def test_post_list_unauthenticated_user(api_client):
    """인증되지 않은 사용자의 게시글 목록 조회 테스트"""
    popular_user = User.objects.create_user(
        username="popularuser", password="pass", email="popularuser@example.com"
    )

    post = Post.objects.create(user=popular_user, content="Post from popular user")

    response = api_client.get(reverse("post-list"))

    # 응답 코드가 200인지 확인 (게시글 목록이 반환되는지 여부 확인)
    assert response.status_code == status.HTTP_200_OK

    # 'results'에 데이터가 있는지 확인
    assert len(response.data["results"]) > 0

    # 게시글의 첫 번째 항목이 예상한 post인지 확인
    assert response.data["results"][0]["id"] == str(post.id)


@pytest.mark.django_db
def test_create_post_with_excess_images(api_client, user, create_temp_image):
    """10개를 초과한 이미지를 포함한 게시글 생성 시 에러 테스트"""
    api_client.force_authenticate(user=user)

    # 'multipart/form-data'로 보내기 위한 데이터 준비
    data = {"content": "Test post", "tags": ["testtag1", "testtag2"]}
    files = {}

    for i in range(12):
        with create_temp_image() as image_path:
            with open(image_path, "rb") as img_file:
                files[f"images_{i}"] = img_file

    response = api_client.post(
        reverse("post-list"), data, format="multipart", files=files
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
