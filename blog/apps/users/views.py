# Python modules
from typing import Any
import logging

# Django modules
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.status import (
    HTTP_201_CREATED, HTTP_200_OK, HTTP_400_BAD_REQUEST,
    HTTP_429_TOO_MANY_REQUESTS
)
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse

# Project modules
from apps.users.models import CustomUser
from apps.users.serializers import (
    UserLoginFailSerializer,
    UserLoginResponseSerializer,
    UserLoginSerializer,
    UserRegisterFailSerializer,
    UserRegisterResponseSerializer,
    UserRegisterSerializer,
    UserPreferredLanguage,
    UserPrefferedTimezone
)
from apps.users.decorator import validate_serializer_data, rate_limit
from apps.service.services import send_welcome_user_email


logger = logging.getLogger(__name__)


class CustomUserViewSet(ViewSet):
    """ViewSet for Custom User handling"""

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary='Login',
        description='Authenticates a user and returns a JWT access and refresh token pair.',
        tags=['Auth'],
        responses={
            HTTP_200_OK: UserLoginResponseSerializer,
            HTTP_400_BAD_REQUEST: UserLoginFailSerializer,
            HTTP_429_TOO_MANY_REQUESTS: OpenApiResponse(
                description='Rate limit exceeded',
                examples=[
                    OpenApiExample(
                        'Too many requests',
                        value={'detail': 'Too many requests. Try again later.'},
                        response_only=True,
                        status_codes=[str(HTTP_429_TOO_MANY_REQUESTS)]
                    )
                ]
            ),
        },
        examples=[
            OpenApiExample(
                'Request body',
                value={'email': 'user@example.com', 'password': 'secret123'},
                request_only=True,
            ),
            OpenApiExample(
                'Success response',
                value={
                    'id': 1,
                    'email': 'user@example.com',
                    'access': 'eyJhbGci...',
                    'refresh': 'eyJhbGci...'
                },
                response_only=True,
                status_codes=[str(HTTP_200_OK)]
            ),
            OpenApiExample(
                'Wrong password',
                value={'password': ['Incorrect password']},
                response_only=True,
                status_codes=[str(HTTP_400_BAD_REQUEST)]
            )
        ]
    )
    @action(methods=('POST',), detail=False, url_path='login', permission_classes=(AllowAny,))
    @validate_serializer_data(serializer_class=UserLoginSerializer)
    @rate_limit('login', limit=10, timeout=60)
    def login(self, request: DRFRequest, *args: tuple, **kwargs: dict) -> DRFResponse:
        """Handle user login."""
        logger.info("User is trying to login into account")

        serializer: UserLoginSerializer = kwargs['serializer']
        user: CustomUser = serializer.validated_data.pop('user')

        refresh_token: RefreshToken = RefreshToken.for_user(user)
        access_token: str = str(refresh_token.access_token)

        return DRFResponse(
            data={
                'id': user.id,
                'email': user.email,
                'access': access_token,
                'refresh': str(refresh_token)
            },
            status=HTTP_200_OK
        )

    @extend_schema(
        summary='Register',
        description=(
            'Creates a new user account. '
            'Sends a welcome email in the user\'s preferred language. '
            'Language must be one of: en, ru, kz. '
            'Timezone must be a valid IANA identifier e.g. Asia/Almaty.'
        ),
        tags=['Auth'],
        responses={
            HTTP_201_CREATED: UserRegisterResponseSerializer,
            HTTP_400_BAD_REQUEST: UserRegisterFailSerializer,
            HTTP_429_TOO_MANY_REQUESTS: OpenApiResponse(description='Rate limit exceeded'),
        },
        examples=[
            OpenApiExample(
                'Request body',
                value={
                    'first_name': 'Rasul',
                    'last_name': 'Bekov',
                    'email': 'rasul@example.com',
                    'password': 'StrongPass123!',
                    'preferred_language': 'ru',
                    'timezone': 'Asia/Almaty'
                },
                request_only=True,
            ),
            OpenApiExample(
                'Created response',
                value={
                    'id': 2,
                    'first_name': 'Rasul',
                    'last_name': 'Bekov',
                    'email': 'rasul@example.com',
                    'preferred_language': 'ru',
                    'timezone': 'Asia/Almaty'
                },
                response_only=True,
                status_codes=[str(HTTP_201_CREATED)]
            ),
            OpenApiExample(
                'Email already exists',
                value={'email': ['This email address rasul@example.com already exist']},
                response_only=True,
                status_codes=[str(HTTP_400_BAD_REQUEST)]
            )
        ]
    )
    @action(methods=('POST',), detail=False, url_path='register', permission_classes=(AllowAny,))
    @validate_serializer_data(serializer_class=UserRegisterSerializer)
    @rate_limit('register', limit=5, timeout=60)
    def register(self, request: DRFRequest, *args: tuple, **kwargs: dict) -> DRFResponse:
        """Handle user registration."""
        logger.info("User trying to register into the service")

        serializer: UserRegisterSerializer = kwargs['serializer']
        data = serializer.validated_data

        user: CustomUser = CustomUser.objects.create_user(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            password=data['password'],
            preferred_language=data.get('preferred_language', 'en'),
            timezone=data.get('timezone', 'UTC')
        )

        send_welcome_user_email(user)

        return DRFResponse(
            data={
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'preferred_language': user.preferred_language,
                'timezone': user.timezone
            },
            status=HTTP_201_CREATED
        )

    @extend_schema(
        summary='Refresh access token',
        description='Returns a new access token given a valid refresh token.',
        tags=['Auth'],
        responses={
            HTTP_200_OK: OpenApiResponse(
                description='New access token',
                examples=[
                    OpenApiExample(
                        'Success',
                        value={'access': 'eyJhbGci...'},
                        response_only=True,
                        status_codes=[str(HTTP_200_OK)]
                    )
                ]
            ),
            HTTP_400_BAD_REQUEST: OpenApiResponse(
                description='Invalid or missing refresh token',
                examples=[
                    OpenApiExample(
                        'Missing token',
                        value={'detail': 'Refresh token required'},
                        response_only=True,
                        status_codes=[str(HTTP_400_BAD_REQUEST)]
                    )
                ]
            ),
        },
        examples=[
            OpenApiExample(
                'Request body',
                value={'refresh': 'eyJhbGci...'},
                request_only=True,
            )
        ]
    )
    @action(methods=['POST'], detail=False, url_path='token/refresh', permission_classes=[AllowAny])
    def refresh_token(self, request: DRFRequest) -> DRFResponse:
        """Return a new access token from a refresh token."""
        refresh = request.data.get('refresh')
        if not refresh:
            return DRFResponse({"detail": _("Refresh token required")}, status=HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh)
            return DRFResponse({"access": str(token.access_token)}, status=HTTP_200_OK)
        except Exception:
            return DRFResponse({"detail": _("Invalid refresh token")}, status=HTTP_400_BAD_REQUEST)


    @extend_schema(
        summary='Update preferred language',
        description="Updates the authenticated user's preferred language. Must be one of: en, ru, kz.",
        tags=['Auth'],
        responses={
            HTTP_200_OK: OpenApiResponse(
                description='Language updated',
                examples=[
                    OpenApiExample(
                        'Success',
                        value={'preferred_language': 'ru'},
                        response_only=True,
                        status_codes=[str(HTTP_200_OK)]
                    )
                ]
            ),
            HTTP_400_BAD_REQUEST: OpenApiResponse(description='Invalid language value'),
        },
        examples=[
            OpenApiExample(
                'Request body',
                value={'preferred_language': 'ru'},
                request_only=True,
            )
        ]
    )
    @action(methods=['PATCH'], detail=False, url_path='auth/language', permission_classes=[IsAuthenticated])
    @validate_serializer_data(serializer_class=UserPreferredLanguage)
    def update_language(self, request: DRFRequest, *args: tuple, **kwargs: dict) -> DRFResponse:
        """Update the authenticated user's preferred language."""
        serializer: UserPreferredLanguage = kwargs['serializer']
        data = serializer.validated_data

        request.user.preferred_language = data.get('preferred_language')
        request.user.save(update_fields=['preferred_language'])

        return DRFResponse(
            {'preferred_language': request.user.preferred_language},
            status=HTTP_200_OK
        )

    @extend_schema(
        summary='Update preferred timezone',
        description="Updates the authenticated user's timezone. Must be a valid IANA timezone e.g. Asia/Almaty, Europe/Moscow.",
        tags=['Auth'],
        responses={
            HTTP_200_OK: OpenApiResponse(
                description='Timezone updated',
                examples=[
                    OpenApiExample(
                        'Success',
                        value={'timezone': 'Asia/Almaty'},
                        response_only=True,
                        status_codes=[str(HTTP_200_OK)]
                    )
                ]
            ),
            HTTP_400_BAD_REQUEST: OpenApiResponse(
                description='Invalid IANA timezone',
                examples=[
                    OpenApiExample(
                        'Invalid timezone',
                        value={'timezone': ['Invalid timezone. Use a valid IANA timezone name, for example: Asia/Almaty.']},
                        response_only=True,
                        status_codes=[str(HTTP_400_BAD_REQUEST)]
                    )
                ]
            ),
        },
        examples=[
            OpenApiExample(
                'Request body',
                value={'timezone': 'Asia/Almaty'},
                request_only=True,
            )
        ]
    )
    @action(methods=['PATCH'], detail=False, url_path='auth/timezone', permission_classes=[IsAuthenticated])
    @validate_serializer_data(serializer_class=UserPrefferedTimezone)
    def update_timezone(self, request: DRFRequest, *args: tuple, **kwargs: dict) -> DRFResponse:
        """Update the authenticated user's preferred timezone."""
        serializer: UserPrefferedTimezone = kwargs['serializer']
        data = serializer.validated_data

        request.user.timezone = data.get('timezone')
        request.user.save(update_fields=['timezone'])

        return DRFResponse(
            {'timezone': request.user.timezone},
            status=HTTP_200_OK
        )