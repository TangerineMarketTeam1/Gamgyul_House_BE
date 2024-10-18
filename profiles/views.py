from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .serializers import (
    ProfileSerializer,
    ProfileUpdateSerializer,
    PrivacySettingsSerializer,
)
from .models import PrivacySettings

User = get_user_model()


class ProfileDetailView(generics.RetrieveAPIView):

    queryset = User.objects.all()
    serializer_class = ProfileSerializer
    authentication_classes = [JWTAuthentication]
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
        return super().get(request, *args, **kwargs)


class ProfileUpdateView(generics.UpdateAPIView):

    serializer_class = ProfileUpdateSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    @extend_schema(
        summary="사용자 프로필 조회",
        description="현재 로그인한 사용자의 프로필 정보를 조회합니다.",
        responses={200: ProfileUpdateSerializer},
        tags=["profile"],
    )
    def get(self, request, *args, **kwargs):
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
        """전체 업데이트"""
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
        """부분 업데이트"""
        return super().partial_update(request, *args, **kwargs)


class PrivacySettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = PrivacySettingsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
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
        return self.partial_update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
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
        instance = serializer.instance
        validated_data = serializer.validated_data
        privacy_settings = validated_data.get("privacy_settings", {})

        for field, audiences in privacy_settings.items():
            for audience, is_visible in audiences.items():
                instance.set_visibility(field, audience, is_visible)

        instance.save()
