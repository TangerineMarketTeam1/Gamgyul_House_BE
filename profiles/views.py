from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .serializers import (
    ProfileSerializer,
    ProfileUpdateSerializer,
    PrivacySettingsSerializer,
)
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from .models import PrivacySettings

User = get_user_model()


class ProfileDetailView(generics.RetrieveAPIView):
    """사용자 프로필 세부 정보를 조회하는 뷰.

    이 뷰는 지정된 사용자 ID에 해당하는 프로필 정보를 반환합니다.
    인증된 사용자만 접근할 수 있습니다.

    Attributes:
        queryset: 모든 User 객체를 포함하는 쿼리셋.
        serializer_class: 프로필 정보를 직렬화하는데 사용되는 시리얼라이저.
        permission_classes: 뷰에 접근하기 위해 필요한 권한.
        lookup_field: 사용자를 식별하는데 사용되는 필드.
    """

    queryset = User.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    @extend_schema(
        summary="사용자 프로필 조회",
        description="지정된 사용자 UUID의 프로필 정보를 조회합니다. 조회자의 권한에 따라 정보 표시가 다를 수 있습니다.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="조회할 사용자의 UUID",
            ),
        ],
        responses={
            200: ProfileSerializer,
            401: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "프로필 조회 성공 예시",
                summary="성공적인 프로필 조회",
                description="사용자 프로필 정보가 성공적으로 조회된 경우",
                value={
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "username": "example_user",
                    "bio": "This is a bio",
                    "profile_image": "http://example.com/profile.jpg",
                    "followers_count": 10,
                    "following_count": 20,
                },
                response_only=True,
            ),
        ],
        tags=["profile"],
    )
    def get(self, request, *args, **kwargs):
        """프로필 정보를 조회합니다.

        Args:
            request: HTTP 요청 객체.
            *args: 추가 인자.
            **kwargs: 추가 키워드 인자.

        Returns:
            Response: 프로필 정보를 포함한 HTTP 응답.
        """
        return super().get(request, *args, **kwargs)


class ProfileUpdateView(generics.UpdateAPIView):
    """사용자 프로필 업데이트 뷰.

    이 뷰는 현재 로그인한 사용자의 프로필 정보를 업데이트합니다.
    인증된 사용자만 접근할 수 있습니다.

    Attributes:
        serializer_class: 프로필 업데이트에 사용되는 시리얼라이저.
        permission_classes: 뷰에 접근하기 위해 필요한 권한.
    """

    serializer_class = ProfileUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """현재 요청을 보낸 사용자 객체를 반환합니다.

        Returns:
            User: 현재 인증된 사용자 객체.
        """
        return self.request.user

    @extend_schema(
        summary="사용자 프로필 조회",
        description="현재 로그인한 사용자의 프로필 정보를 조회합니다.",
        responses={200: ProfileUpdateSerializer},
        tags=["profile"],
    )
    def get(self, request, *args, **kwargs):
        """현재 사용자의 프로필 정보를 조회합니다.

        Args:
            request: HTTP 요청 객체.
            *args: 추가 인자.
            **kwargs: 추가 키워드 인자.

        Returns:
            Response: 프로필 정보를 포함한 HTTP 응답.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(
        summary="사용자 프로필 전체 업데이트",
        description="현재 로그인한 사용자의 프로필 정보를 전체 업데이트합니다.",
        request=ProfileUpdateSerializer,
        responses={200: ProfileUpdateSerializer},
        examples=[
            OpenApiExample(
                "프로필 업데이트 예시",
                value={
                    "bio": "새로운 자기소개",
                    "username": "newuser",
                },
                request_only=True,
            )
        ],
        tags=["profile"],
    )
    def put(self, request, *args, **kwargs):
        """사용자 프로필 정보를 전체 업데이트합니다.

        Args:
            request: HTTP 요청 객체.
            *args: 추가 인자.
            **kwargs: 추가 키워드 인자.

        Returns:
            Response: 업데이트된 프로필 정보를 포함한 HTTP 응답.
        """
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="사용자 프로필 부분 업데이트",
        description="현재 로그인한 사용자의 프로필 정보를 부분적으로 업데이트합니다.",
        request=ProfileUpdateSerializer,
        responses={200: ProfileUpdateSerializer},
        examples=[
            OpenApiExample(
                "프로필 부분 업데이트 예제",
                value={
                    "bio": "새로운 자기소개",
                },
                request_only=True,
            )
        ],
        tags=["profile"],
    )
    def patch(self, request, *args, **kwargs):
        """사용자 프로필 정보를 부분적으로 업데이트합니다.

        Args:
            request: HTTP 요청 객체.
            *args: 추가 인자.
            **kwargs: 추가 키워드 인자.

        Returns:
            Response: 부분 업데이트된 프로필 정보를 포함한 HTTP 응답.
        """
        return super().partial_update(request, *args, **kwargs)


class PrivacySettingsView(generics.RetrieveUpdateAPIView):
    """사용자 프라이버시 설정 뷰.

    이 뷰는 사용자의 프라이버시 설정을 조회하고 업데이트합니다.
    인증된 사용자만 자신의 설정에 접근할 수 있습니다.

    Attributes:
        serializer_class: 프라이버시 설정을 직렬화하는데 사용되는 시리얼라이저.
        permission_classes: 뷰에 접근하기 위해 필요한 권한.
    """

    serializer_class = PrivacySettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """현재 요청에 해당하는 PrivacySettings 객체를 반환합니다.

        Returns:
            PrivacySettings: 요청된 사용자의 프라이버시 설정 객체.

        Raises:
            PermissionDenied: 요청한 사용자가 설정의 소유자가 아닌 경우.
            Http404: 요청된 사용자를 찾을 수 없는 경우.
        """
        user_id = self.kwargs.get("user_id")
        user = get_object_or_404(User, id=user_id)

        if self.request.user != user:
            raise PermissionDenied(
                "You don't have permission to access these settings."
            )

        return PrivacySettings.objects.get_or_create(user=user)[0]

    @extend_schema(
        summary="프로필 보안 설정 조회",
        description="현재 사용자의 프로필 보안 설정을 조회합니다.",
        parameters=[
            OpenApiParameter(
                name="user_id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="설정을 조회할 사용자의 UUID",
            ),
        ],
        responses={
            status.HTTP_200_OK: PrivacySettingsSerializer,
            status.HTTP_401_UNAUTHORIZED: OpenApiTypes.OBJECT,
            status.HTTP_403_FORBIDDEN: OpenApiTypes.OBJECT,
            status.HTTP_404_NOT_FOUND: OpenApiTypes.OBJECT,
        },
        tags=["profile"],
    )
    def get(self, request, *args, **kwargs):
        """현재 사용자의 프라이버시 설정을 조회합니다.

        Args:
            request: HTTP 요청 객체.
            *args: 추가 인자.
            **kwargs: 추가 키워드 인자.

        Returns:
            Response: 프라이버시 설정 정보를 포함한 HTTP 응답.
        """
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="프로필 보안 설정 업데이트",
        description="현재 사용자의 프로필 보안 설정을 업데이트합니다.",
        request=PrivacySettingsSerializer,
        responses={
            status.HTTP_200_OK: PrivacySettingsSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiTypes.OBJECT,
            status.HTTP_401_UNAUTHORIZED: OpenApiTypes.OBJECT,
            status.HTTP_403_FORBIDDEN: OpenApiTypes.OBJECT,
            status.HTTP_404_NOT_FOUND: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "유효한 입력",
                value={
                    "privacy_settings": {
                        "email": {
                            "followers": True,
                            "following": True,
                            "others": False,
                        },
                        "bio": {"followers": True, "following": True, "others": True},
                        "posts": {
                            "followers": True,
                            "following": True,
                            "others": False,
                        },
                        "following_list": {
                            "followers": True,
                            "following": True,
                            "others": False,
                        },
                        "follower_list": {
                            "followers": True,
                            "following": True,
                            "others": False,
                        },
                    }
                },
                request_only=True,
            ),
        ],
        tags=["profile"],
    )
    def put(self, request, *args, **kwargs):
        """사용자의 프라이버시 설정을 전체 업데이트합니다.

        Args:
            request: HTTP 요청 객체.
            *args: 추가 인자.
            **kwargs: 추가 키워드 인자.

        Returns:
            Response: 업데이트된 프라이버시 설정 정보를 포함한 HTTP 응답.
        """
        return self.update(request, *args, **kwargs)

    @extend_schema(
        summary="프로필 보안 설정 부분 업데이트",
        description="현재 사용자의 프로필 보안 설정을 부분적으로 업데이트합니다.",
        request=PrivacySettingsSerializer,
        responses={
            status.HTTP_200_OK: PrivacySettingsSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiTypes.OBJECT,
            status.HTTP_401_UNAUTHORIZED: OpenApiTypes.OBJECT,
            status.HTTP_403_FORBIDDEN: OpenApiTypes.OBJECT,
            status.HTTP_404_NOT_FOUND: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "유효한 부분 입력",
                value={
                    "privacy_settings": {
                        "email": {"followers": False},
                        "posts": {"others": True},
                    }
                },
                request_only=True,
            ),
        ],
        tags=["profile"],
    )
    def patch(self, request, *args, **kwargs):
        """사용자의 프라이버시 설정을 부분적으로 업데이트합니다.

        Args:
            request: HTTP 요청 객체.
            *args: 추가 인자.
            **kwargs: 추가 키워드 인자.

        Returns:
            Response: 부분 업데이트된 프라이버시 설정 정보를 포함한 HTTP 응답.
        """
        return self.partial_update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """프라이버시 설정을 업데이트합니다.

        Args:
            request: HTTP 요청 객체.
            *args: 추가 인자.
            **kwargs: 추가 키워드 인자.

        Returns:
            Response: 업데이트 결과를 포함한 HTTP 응답.

        Raises:
            ValidationError: 입력 데이터가 유효하지 않은 경우.
        """
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "detail": "프로필 보안 설정이 성공적으로 업데이트되었습니다.",
                "data": serializer.data,
            }
        )

    def perform_update(self, serializer):
        """프라이버시 설정 업데이트를 수행합니다.

        이 메서드는 검증된 데이터를 사용하여 프라이버시 설정을 실제로 업데이트합니다.

        Args:
            serializer: 유효성이 검증된 시리얼라이저 인스턴스.
        """
        instance = serializer.instance
        validated_data = serializer.validated_data
        privacy_settings = validated_data.get("privacy_settings", {})

        for field, audiences in privacy_settings.items():
            for audience, is_visible in audiences.items():
                instance.set_visibility(field, audience, is_visible)

        instance.save()
