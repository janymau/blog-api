# Python modules
# Django modules
from django.utils import translation
from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async

# Rest framework modules
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse

SUPPORTED_LANGUAGE = {"en", "ru", "kz"}

class UserLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: DRFRequest):
        lang: str = self._resolve(request)

        if lang:
            translation.activate(lang)
            request.LANGUAGE_CODE = lang

        response: DRFResponse = self.get_response(request)
        translation.deactivate()

        return response

    def _get_jwt_user(self, request):
        from rest_framework_simplejwt.authentication import JWTAuthentication
        authenticator = JWTAuthentication()
        try:
            result = authenticator.authenticate(request)
            if result is not None:
                return result[0]
        except Exception as e:
            print("JWT auth error:", e)
        return None

    def _resolve(self, request: DRFRequest) -> str | None:
        from apps.users.models import CustomUser  # ← moved here
        user = self._get_jwt_user(request)
        if user and user.is_authenticated:
            lang: str = getattr(user, 'preferred_language', None)
            if lang in SUPPORTED_LANGUAGE:
                return lang

        lang: str = request.GET.get('lang', '').lower()
        if lang in SUPPORTED_LANGUAGE:
            return lang

        return None


class JWTAuthUserMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        from django.contrib.auth.models import AnonymousUser
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
        from apps.users.models import CustomUser  # ← moved here

        @database_sync_to_async
        def get_user_by_token(token: str):
            try:
                validated = AccessToken(token)
                return CustomUser.objects.get(id=validated['user_id'])
            except (InvalidToken, TokenError, CustomUser.DoesNotExist):
                return AnonymousUser()

        query_string = parse_qs(scope['query_string'].decode())
        token = query_string.get('token', [None])[0]

        scope['user'] = await get_user_by_token(token) if token else AnonymousUser()

        return await super().__call__(scope, receive, send)