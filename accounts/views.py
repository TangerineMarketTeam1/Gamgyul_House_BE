from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from dj_rest_auth.views import LoginView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import CustomLoginSerializer
from profiles.serializers import ProfileSerializer


class GoogleLogin(SocialLoginView):
    """
    Google OAuth2를 통한 소셜 로그인을 처리하는 뷰.

    이 클래스는 Google OAuth2 어댑터를 사용하여 사용자 인증을 처리합니다.

    Attributes:
        adapter_class (GoogleOAuth2Adapter): Google OAuth2 인증을 위한 어댑터 클래스.
        callback_url (str): 인증 후 리다이렉트될 URL.
        client_class (OAuth2Client): OAuth2 클라이언트 클래스.
    """

    adapter_class = GoogleOAuth2Adapter
    callback_url = (
        "http://localhost:8000/accounts/google/callback/"  # 프론트엔드 URL로 변경 필요
    )
    client_class = OAuth2Client


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
