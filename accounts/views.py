from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from dj_rest_auth.views import LoginView
from .serializers import CustomLoginSerializer


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = (
        "http://localhost:8000/accounts/google/callback/"  # 프론트엔드 URL로 변경 필요
    )
    client_class = OAuth2Client


class CustomLoginView(LoginView):
    serializer_class = CustomLoginSerializer
