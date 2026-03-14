# Python modules
from typing import Any

# Django modules
from django.utils import translation

# Rest framework modules
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework_simplejwt.authentication import JWTAuthentication

# Project modules
from apps.users.models import CustomUser

SUPPORTED_LANGUAGE = {"en", "ru", "kz"}

class UserLanguageMiddleware:
    """
    Resolve the active language for every request using this priority:
    1. Authenticated user's saved preferred_language
    2. ?lang= query parameter
    3. Accept-Language header (handled by Django's LocaleMiddleware after us)
    4. settings.LANGUAGE_CODE
    """

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

    def _get_jwt_user(self, request) -> CustomUser | None:
        """Authenticate via JWT without modifying request.user."""
        authenticator = JWTAuthentication()
        try:
            result = authenticator.authenticate(request)
            if result is not None:
                return result[0] 
        except Exception as e:
            print("JWT auth error:", e)
        return None

    def _resolve(self, request: DRFRequest) -> str | None:
        user = self._get_jwt_user(request)
        if user and user.is_authenticated:
            lang: str = getattr(user, 'preferred_language', None)
            if lang in SUPPORTED_LANGUAGE:
                return lang

        lang: str = request.GET.get('lang', '').lower()
        if lang in SUPPORTED_LANGUAGE:
            return lang

        return None