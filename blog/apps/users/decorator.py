# Python modules
from functools import wraps
from typing import Any, Optional, Callable, Type, TypeVar


# Django modules
from django.db.models import Model, Manager, QuerySet
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.serializers import Serializer
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_429_TOO_MANY_REQUESTS
from django.core.cache import cache



# Project modules 



T = TypeVar('T', bound=Model)

def validate_serializer_data(
        serializer_class: Serializer = Type[Serializer],
        context : Optional[dict[str, Any]] = None,
        many : bool = False
) -> Callable:
    """Decorator to preprocess the request data validation"""

    def decorator(
            func : Callable[[DRFRequest, tuple[Any, ...], dict[str, Any]], DRFResponse],
              ) -> Callable:
        
        @wraps(func)
        def wrapper(
            self,
            request : DRFRequest,
            *args : tuple[Any, ...],
            **kwargs : dict[str, Any]
        ):
            """Validate the request data using the provided serializer class"""
            local_context : dict[str, Any] = context or {}
            local_context['request'] = request

            data: dict[str, Any] = {}
            if request.method in ("POST", "PUT", "PATCH"):
                data = request.data
            else:
                data = request.query_params

            if 'pk' in kwargs:
                local_context['pk'] = int(kwargs['pk'])

            if 'object' in kwargs:
                local_context['object'] = kwargs['object']

            serializer : Serializer = serializer_class(
                instance = getattr(local_context, 'object', None),
                data=data,
                context = local_context,
                many = many,
                partial = request.method == 'PATCH'

            )

            if serializer.is_valid():
                kwargs['validated_data'] = serializer.validated_data.copy()
                kwargs['serializer'] = serializer
                return func(self, request, *args, **kwargs)
            else:
                return DRFResponse(
                    data=serializer.errors,
                    status=HTTP_400_BAD_REQUEST
                )
        return wrapper
    return decorator
def rate_limit(key_prefix, limit, timeout):
    """Decorator for user request limit"""

    def decorator(func):
        @wraps(func)

        def wrapper(
            self,
            request: DRFRequest,
            *args: tuple[Any, ...],
            **kwargs: dict[str, Any]
        ):
            if request.user.is_authenticated:
                key = f"{key_prefix}:{request.user.id}"
            else:
                ip = request.META.get("REMOTE_ADDR", "")
                key = f"{key_prefix}:{ip}"

            count = cache.get(key, 0)

            if count >= limit:
                return DRFResponse(
                    {"detail": "Too many requests. Try again later."},
                    status=HTTP_429_TOO_MANY_REQUESTS
                )

            if count == 0:
                cache.set(key, 1, timeout=timeout)
            else:
                cache.incr(key)

            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator