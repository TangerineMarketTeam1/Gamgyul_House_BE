from dj_rest_auth.serializers import LoginSerializer
from django.contrib.auth import get_user_model
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
