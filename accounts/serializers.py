from django.contrib.auth import get_user_model

from dj_rest_auth.serializers import LoginSerializer
from dj_rest_auth.registration.serializers import SocialLoginSerializer
from rest_framework import serializers

from .models import CustomUser


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "username", "profile_image"]


class CustomLoginSerializer(LoginSerializer):
    """이메일과 비밀번호를 사용한 사용자 로그인을 위한 커스텀 serializer.

    이 serializer는 기본 LoginSerializer를 확장하여 username 대신 email을 사용합니다.

    Attributes:
        email (EmailField): 사용자의 이메일 주소.
        password (CharField): 사용자의 비밀번호. write_only로 설정되어 있습니다.
    """

    username = None
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        """제공된 이메일과 비밀번호의 유효성을 검사합니다.

        이 메서드는 주어진 이메일 주소로 사용자를 찾고,
        비밀번호가 일치하는지 확인합니다.

        Args:
            attrs (dict): 검증할 속성들의 딕셔너리.

        Returns:
            dict: 유효한 경우, 'user' 키가 추가된 속성 딕셔너리.

        Raises:
            serializers.ValidationError: 이메일 또는 비밀번호가 유효하지 않은 경우.
        """
        email = attrs.get("email")
        password = attrs.get("password")

        user = get_user_model().objects.filter(email=email).first()

        if user and user.check_password(password):
            attrs["user"] = user
            return attrs

        raise serializers.ValidationError("Invalid email or password.")


class CustomSocialLoginSerializer(SocialLoginSerializer):
    """소셜 로그인 과정에서 필요한 토큰 검증과 사용자 처리를 담당하는 시리얼라이저.

    SocialLoginSerializer를 상속받아 Google OAuth 토큰 검증 중 발생할 수 있는
    TypeError를 처리합니다. 이는 dj-rest-auth의 기본 serializer가 access_token만으로는
    처리하지 못하는 Google OAuth의 특수한 토큰 형식을 지원하기 위함입니다.

    일반적인 OAuth 처리 과정:
    1. 프론트엔드로부터 받은 access_token 확인
    2. Google OAuth adapter를 통해 토큰 검증
    3. 검증된 토큰으로 소셜 로그인 진행
    4. 필요한 경우 새 사용자 생성
    """

    def validate(self, attrs):
        """소셜 로그인 토큰을 검증하고 사용자 객체를 반환합니다.

        Args:
            attrs (dict): 검증할 데이터. access_token을 포함해야 함

        Returns:
            dict: 검증된 데이터와 사용자 객체

        Raises:
            ValidationError: view나 adapter_class가 없거나 access_token이 없는 경우
        """
        try:
            return super().validate(attrs)
        except TypeError:
            view = self.context.get("view")
            request = self._get_request()

            if not view:
                raise serializers.ValidationError(
                    "View is not defined, pass it as a context variable"
                )

            adapter_class = getattr(view, "adapter_class", None)
            if not adapter_class:
                raise serializers.ValidationError("Define adapter_class in view")

            adapter = adapter_class(request)
            app = adapter.get_provider().app

            access_token = attrs.get("access_token")
            if not access_token:
                raise serializers.ValidationError(
                    "Incorrect input. access_token is required."
                )

            social_token = adapter.parse_token({"access_token": access_token})
            social_token.app = app

            login = self.get_social_login(adapter, app, social_token, access_token)
            ret = self.complete_social_login(request, login)

            if not login.is_existing:
                login.lookup()
                login.save(request, connect=True)

            attrs["user"] = login.account.user
            return attrs
