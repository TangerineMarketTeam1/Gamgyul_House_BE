from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from dj_rest_auth.views import LoginView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from profiles.serializers import ProfileSerializer
from .serializers import (
    CustomLoginSerializer,
    CustomSocialLoginSerializer,
    SimpleUserSerializer,
)

User = get_user_model()


class GoogleLogin(SocialLoginView):
    """Google OAuth2를 이용한 소셜 로그인을 처리하는 뷰.

    SocialLoginView를 상속받아 Google OAuth2 인증을 처리하고 JWT 토큰을 발급합니다.

    Attributes:
        client_class: OAuth2 클라이언트 클래스
        adapter_class: Google OAuth2 어댑터 클래스
        callback_url: Google OAuth 콜백 URL
        serializer_class: 소셜 로그인 시리얼라이저
    """

    client_class = OAuth2Client
    adapter_class = GoogleOAuth2Adapter
    callback_url = settings.GOOGLE_CALLBACK_URI
    serializer_class = CustomSocialLoginSerializer

    def get_response(self):
        """JWT 토큰이 포함된 응답을 반환합니다.

        Returns:
            Response: JWT access/refresh 토큰과 사용자 정보가 포함된 응답
        """
        response = super().get_response()

        # JWT 토큰 생성
        if self.user:
            refresh = RefreshToken.for_user(self.user)
            response.data = {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": str(self.user.id),
                    "email": self.user.email,
                    "username": self.user.username,
                },
            }

        return response

    def post(self, request, *args, **kwargs):
        """Google access token으로 인증을 처리하고 결과를 반환합니다.

        Args:
            request: HTTP 요청 객체

        Returns:
            Response: 인증 결과 또는 에러 응답
        """
        try:
            response = super().post(request, *args, **kwargs)
            print("Response data from post:", response.data)
            return response

        except Exception as e:
            print("Error in GoogleLogin:", str(e))
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def get_error_response(self, error):
        """에러 응답을 생성합니다.

        Args:
            error: 발생한 에러 객체

        Returns:
            Response: 에러 메시지와 400 상태 코드를 포함한 응답
        """
        return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)


class CustomLoginView(LoginView):
    """
    사용자 정의 로그인 뷰.

    이 클래스는 기본 LoginView를 확장하여 커스텀 로그인 시리얼라이저를 사용합니다.

    Attributes:
        serializer_class (CustomLoginSerializer): 사용자 정의 로그인 시리얼라이저 클래스.
    """

    serializer_class = CustomLoginSerializer


class CurrentUserView(APIView):
    """
    현재 인증된 사용자의 프로필 정보를 제공하는 뷰.

    이 뷰는 인증된 사용자만 접근할 수 있으며, 사용자의 프로필 정보를 반환합니다.

    Attributes:
        permission_classes (list): 뷰에 접근 가능한 권한 클래스 목록.

    Methods:
        get(request): 현재 인증된 사용자의 프로필 정보를 반환합니다.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        현재 인증된 사용자의 프로필 정보를 조회합니다.

        Args:
            request (HttpRequest): HTTP 요청 객체.

        Returns:
            Response: 사용자 프로필 정보가 포함된 Response 객체.
        """
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)


class UserDetailView(APIView):
    """사용자 상세 정보를 조회하는 뷰.

    Attributes:
        permission_classes: 인증된 사용자만 접근 가능
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, username):
        """사용자 정보를 조회합니다.

        Args:
            request: HTTP 요청 객체
            username: 조회할 사용자의 username

        Returns:
            Response: 사용자 정보 데이터
            Response: 404 에러 (사용자가 존재하지 않는 경우)
        """
        try:
            user = User.objects.get(username=username)
            serializer = SimpleUserSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )


class PasswordChangeView(APIView):
    """비밀번호 변경을 처리하는 뷰.

    Attributes:
        permission_classes: 인증된 사용자만 접근 가능
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """비밀번호 변경을 처리합니다.

        Args:
            request: HTTP 요청 객체 (old_password, new_password1, new_password2 포함)

        Returns:
            Response: 성공 메시지와 200 상태코드
            Response: 400 에러 (유효성 검사 실패 시)

        Raises:
            ValidationError: 비밀번호 유효성 검사 실패 시
        """
        user = request.user
        old_password = request.data.get("old_password")
        new_password1 = request.data.get("new_password1")
        new_password2 = request.data.get("new_password2")

        # 필수 필드 체크
        if not all([old_password, new_password1, new_password2]):
            return Response(
                {"detail": "모든 필드를 입력해주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 현재 비밀번호 확인
        if not user.check_password(old_password):
            return Response(
                {"detail": "현재 비밀번호가 올바르지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 새 비밀번호 일치 확인
        if new_password1 != new_password2:
            return Response(
                {"detail": "새 비밀번호가 일치하지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 새 비밀번호 유효성 검사
        try:
            validate_password(new_password1, user)
        except ValidationError as e:
            return Response({"detail": e.messages}, status=status.HTTP_400_BAD_REQUEST)

        # 비밀번호 변경
        user.set_password(new_password1)
        user.save()

        return Response(
            {"detail": "비밀번호가 성공적으로 변경되었습니다."},
            status=status.HTTP_200_OK,
        )
