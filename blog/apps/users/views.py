# Python modules
from typing import Any
import logging


# Django modules
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken 
from rest_framework_simplejwt.tokens import AccessToken 
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK,HTTP_400_BAD_REQUEST, HTTP_405_METHOD_NOT_ALLOWED
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenRefreshView

# Project modules
from apps.users.models import CustomUser
from apps.users.serializers import (
    UserLoginFailSerializer, 
    UserLoginResponseSerializer,
    UserLoginSerializer, 
    HTTP405MethodNowAllowedSerializer,
    UserRegisterFailSerializer,
    UserRegisterResponseSerializer,
    UserRegisterSerializer
)
from apps.users.decorator import validate_serializer_data, rate_limit


logger = logging.getLogger(__name__)
class CustomUserViewSet(ViewSet):
    """ViewSet for Custom User handling"""
    logger.debug("User entered CustomUserViewSet view")

    permission_classes = (IsAuthenticated,)

    @action(
        methods=('POST', ),
        detail=False,
        url_name='login',
        url_path='login',
        permission_classes = (AllowAny,)
    )

    @validate_serializer_data(serializer_class=UserLoginSerializer)
    @rate_limit('login', limit=10, timeout=60)
    def login(
        self,
        request : DRFRequest,
        *args: tuple[Any, ...],
        **kwargs : dict[str, Any]
    ) -> DRFResponse :
        logger.info(f"User is trying to login into account")
        """
        Handle user login.
        Parameters:
            request: DRFRequest
                The request object.
            *args: tuple
                Additional positional arguments.
            **kwargs: dict
                Additional keyword arguments.

        Returns:
            DRFResponse
                Response containing user data or error message.
        """


        serializer : UserLoginSerializer = kwargs['serializer']

        user : CustomUser = serializer.validated_data.pop('user')

        # Generate JWT Token

        refresh_token: RefreshToken = RefreshToken.for_user(user)
        access_token : str = str(refresh_token.access_token)


        return DRFResponse(
            data={
            'id' : user.id,
            'email' : user.email,
            'access' : access_token,
            "refresh" : str(refresh_token)
            },
            status=HTTP_200_OK
            
        )
    
    @action(
            methods=('POST', ),
            detail=False,
            url_name='register',
            url_path='register',
            permission_classes = (AllowAny,)
    )
    @validate_serializer_data(serializer_class=UserRegisterSerializer)
    @rate_limit('register', limit=5, timeout=60)
    
    def register(
        self,
        request : DRFRequest,
        *args : tuple[Any, ...],
        **kwargs : dict[str, Any]
    ) -> DRFResponse:
        logger.info(f"User trying to register into the service")
        """
        POST method to CustomUser objects
        
        :param self: Description
        :param request: Description
        :type request: DRFRequest
        :param args: Description
        :type args: tuple[Any, ...]
        :param kwargs: Description
        :type kwargs: dict[str, Any]
        :return: Description
        :rtype: Response
        """

        serializer : UserRegisterSerializer = kwargs['serializer'] 
        data = serializer.validated_data

        user : CustomUser = CustomUser.objects.create_user(
            first_name = data['first_name'],
            last_name = data['last_name'],
            email = data['email'],
            password = data['password']
        )

        return DRFResponse(
            data = {
                "id" : user.id,
                'first_name' : user.first_name,
                "last_name" : user.last_name,
                "email" : user.email,
            },
            status=HTTP_201_CREATED
        )
    @action(
        methods=['POST'],
        detail=False, url_path='token/refresh',
        permission_classes=[AllowAny]
    )
    def refresh_token(self, request):
        refresh = request.data.get('refresh')
        if not refresh:
            return DRFResponse({"detail": "Refresh token required"}, status=400)

        try:
            token = RefreshToken(refresh)
            return DRFResponse({"access": str(token.access_token)})
        except Exception:
            return DRFResponse({"detail": "Invalid refresh token"}, status=400)
    
