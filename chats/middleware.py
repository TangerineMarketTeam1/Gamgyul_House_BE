# chats/middleware.py
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs

User = get_user_model()


class JWTAuthMiddleware(BaseMiddleware):
    """JWT 토큰을 사용하여 WebSocket 연결에 대한 사용자 인증을 처리하는 미들웨어.

    Django Channels의 WebSocket 연결은 HTTP와 달리 표준 인증 미들웨어를 사용할 수 없습니다.
    이 미들웨어는 WebSocket URL의 쿼리 파라미터로 전달된 JWT 토큰을 검증하고,
    인증된 사용자 정보를 WebSocket scope에 추가합니다.

    Attributes:
        None

    Methods:
        __call__: WebSocket 연결 요청을 처리하고 사용자 인증을 수행합니다.
        get_user: 주어진 user_id로 데이터베이스에서 사용자를 조회합니다.
    """

    async def __call__(self, scope, receive, send):
        """WebSocket 연결 요청을 처리하고 JWT 토큰 기반 인증을 수행합니다.

        Args:
            scope (dict): WebSocket 연결 scope 정보가 포함된 딕셔너리
            receive (callable): WebSocket으로부터 메시지를 수신하는 비동기 함수
            send (callable): WebSocket으로 메시지를 전송하는 비동기 함수

        Returns:
            callable: 다음 미들웨어 또는 consumer를 실행하는 코루틴

        Notes:
            - URL 쿼리 파라미터에서 'token' 값을 추출합니다.
            - 토큰이 유효한 경우 해당 사용자 객체를 scope['user']에 저장합니다.
            - 토큰이 없거나 유효하지 않은 경우 AnonymousUser를 설정합니다.
        """
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]

        if token:
            try:
                access_token = AccessToken(token)
                user = await self.get_user(access_token["user_id"])
                scope["user"] = user
            except Exception as e:
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user(self, user_id):
        """주어진 user_id에 해당하는 사용자를 데이터베이스에서 조회합니다.

        Args:
            user_id (uuid): 조회할 사용자의 UUID

        Returns:
            User: 조회된 사용자 객체
            AnonymousUser: 사용자를 찾을 수 없는 경우 반환되는 익명 사용자 객체

        Notes:
            - 데이터베이스 조회를 위해 @database_sync_to_async 데코레이터를 사용합니다.
            - 사용자를 찾을 수 없는 경우 AnonymousUser를 반환합니다.
        """
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return AnonymousUser()
