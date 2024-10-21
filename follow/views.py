from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
    OpenApiExample,
    OpenApiResponse,
)
from .models import Follow
from .serializers import FollowSerializer
from profiles.serializers import ProfileSerializer

User = get_user_model()


class FollowView(generics.CreateAPIView):
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="사용자 팔로우",
        description="특정 사용자를 팔로우합니다. 자기 자신을 팔로우하거나 이미 팔로우한 사용자를 다시 팔로우할 수 없습니다.",
        parameters=[
            OpenApiParameter(
                name="pk",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="팔로우할 사용자의 UUID",
            ),
        ],
        responses={
            status.HTTP_201_CREATED: OpenApiTypes.OBJECT,
            status.HTTP_400_BAD_REQUEST: OpenApiTypes.OBJECT,
            status.HTTP_401_UNAUTHORIZED: OpenApiTypes.OBJECT,
            status.HTTP_404_NOT_FOUND: OpenApiTypes.OBJECT,
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "성공 응답",
                value={
                    "id": 2,
                    "username": "user2",
                    "bio": "Hello, I'm User Two",
                    "profile_image": "http://example.com/media/profile_images/user2.jpg",
                    "followers": [
                        {
                            "id": "1",
                            "username": "user1",
                            "profile_image": "http://example.com/media/profile_images/user1.jpg",
                        }
                    ],
                    "following": [],
                    "followers_count": 1,
                    "following_count": 0,
                    "commented_posts": [],
                    "products": [],
                },
                response_only=True,
                status_codes=["201"],
            ),
            OpenApiExample(
                "오류: 자기 팔로우",
                value={"detail": "자기 자신을 팔로우할 수 없습니다."},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "오류: 이미 팔로우 중",
                value={"detail": "이미 팔로우한 사용자입니다."},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "오류: 사용자를 찾을 수 없음",
                value={"detail": "팔로우하려는 사용자를 찾을 수 없습니다."},
                response_only=True,
                status_codes=["404"],
            ),
            OpenApiExample(
                "오류: 서버 오류",
                value={"detail": "팔로우 처리 중 오류가 발생했습니다."},
                response_only=True,
                status_codes=["500"],
            ),
        ],
        tags=["follow"],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        팔로우할 아이디 pk(id)값 불러오기
        팔로우할 사용자가 존재하는지 확인
        자기 자신을 팔로우하려는 경우 예외 처리 후 팔로우 관계 생성 시도
        나머지(사용자를 못찾을 때, 이미 팔로우한 사람, 서버 오류) 예외 처리
        """
        try:
            following_id = self.kwargs["pk"]
            following_user = User.objects.get(id=following_id)
            if request.user.id == following_user.id:
                return Response(
                    {"detail": "자기 자신을 팔로우할 수 없습니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            follow, created = Follow.objects.get_or_create(
                follower=request.user, following=following_user
            )

            if created:
                serializer = self.get_serializer(follow)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {"detail": "이미 팔로우한 사용자입니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except User.DoesNotExist:
            return Response(
                {"detail": "팔로우하려는 사용자를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"detail": f"팔로우 처리 중 오류가 발생했습니다: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    summary="언팔로우",
    description="특정 사용자를 언팔로우합니다.",
    parameters=[
        OpenApiParameter(
            name="pk",
            description="언팔로우할 사용자의 UUID",
            required=True,
            type=OpenApiTypes.UUID,
        ),
    ],
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=ProfileSerializer,
            description="언팔로우 성공 및 해당 사용자의 프로필 정보 반환",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="팔로우한 사용자를 찾을 수 없음"
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="이미 팔로우하지 않은 사용자"
        ),
    },
    tags=["follow"],
)
class UnfollowView(generics.DestroyAPIView):
    queryset = Follow.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        """
        팔로우 관계가 있는 유저의 id 값 저장 후
        id 값으로 팔로워를 찾고 삭제
        유저, 팔로우 관계 예외처리
        """
        following_id = self.kwargs["pk"]

        try:
            following_user = User.objects.get(id=following_id)
            follow = Follow.objects.get(
                follower=self.request.user, following=following_user
            )
            follow.delete()
            profile_serializer = self.get_serializer(
                following_user, context={"request": request}
            )
            return Response(profile_serializer.data)

        except User.DoesNotExist:
            return Response(
                {"detail": "언팔로우할 유저가 존재하지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Follow.DoesNotExist:
            return Response(
                {"detail": "현재 유저를 팔로우하고 있지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class FollowerListView(generics.ListAPIView):
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="팔로워 목록 조회",
        description="현재 사용자의 팔로워 목록을 조회합니다.",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=FollowSerializer(many=True),
                description="팔로워 목록",
            ),
        },
        tags=["follow"],
    )
    def list(self, request, *args, **kwargs):
        followers = request.user.followers.all().select_related("follower")
        serializer = self.get_serializer(
            [follow.follower for follow in followers], many=True
        )
        return Response(serializer.data)


class FollowingListView(generics.ListAPIView):
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="팔로잉 목록 조회",
        description="현재 사용자가 팔로우하는 사용자 목록을 조회합니다.",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=FollowSerializer(many=True),
                description="팔로잉 목록",
            ),
        },
        tags=["follow"],
    )
    def list(self, request, *args, **kwargs):
        following = request.user.following.all().select_related("following")
        serializer = self.get_serializer(
            [follow.following for follow in following], many=True
        )
        return Response(serializer.data)
