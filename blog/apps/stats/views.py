# Python modules
from typing import Any, Optional
import pytz
import asyncio
import httpx
from asgiref.sync import async_to_sync, sync_to_async

# Django modules
from rest_framework.serializers import (
    Serializer,
    FloatField,
    IntegerField,
    CharField
)
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext
from django.utils.formats import date_format as django_date_format
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.cache import cache


# Project modules
from apps.blogs.models import Category,Tag,Comment, Post, CustomUser
from apps.users.serializers import UserForeignSerializer


class BlogStatsSerializer(Serializer):
    total_posts = IntegerField()
    total_comments = IntegerField()
    total_users = IntegerField()

class ExchangeCurrencySerializer(Serializer):
    KZT = FloatField()
    RUB = FloatField()
    USD = FloatField()
    
class StatsResponseSerializer(Serializer):
    blog = BlogStatsSerializer()
    exchange_rates = ExchangeCurrencySerializer()
    current_time = CharField()

class StatsErrorSerializer(Serializer):
    detail = CharField()

async def fetch_exchange_rates(
        client : httpx.AsyncClient
) -> dict:
    response = await client.get("https://open.er-api.com/v6/latest/USD")
    response.raise_for_status()

    data = response.json()
    rates = data['rates']

    return {
        "KZT" : rates['KZT'],
        "RUB" : rates['RUB'],
        "EUR" : rates['EUR'],
           
    }

async def fetch_current_time (
    client : httpx.AsyncClient
) -> str:
    response = await client.get("https://timeapi.io/api/time/current/zone?timeZone=Asia/Almaty")
    response.raise_for_status()

    data = response.json()

    return data['dateTime']

async def fetch_blog_count() -> dict:
    from asgiref.sync import sync_to_async

    total_posts    = await sync_to_async(Post.objects.count)()
    total_comments = await sync_to_async(Comment.objects.count)()
    total_users    = await sync_to_async(CustomUser.objects.count)()

    return {
        "total_posts": total_posts,
        "total_comments": total_comments,
        "total_users": total_users,
    }

async def build_stats_payload() -> dict:
    cache_key = "stats_payload"

    cached = await sync_to_async(cache.get)(cache_key)
    if cached is not None:
        return cached

    timeout = httpx.Timeout(10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        exchange_rates, current_time, blog_counts = await asyncio.gather(
            fetch_exchange_rates(client),
            fetch_current_time(client),
            fetch_blog_count(),
        )

    payload = {
        "blog":           blog_counts,
        "exchange_rates": exchange_rates,
        "current_time":   current_time,
    }

    # Cache for 60 seconds — rates don't change faster than that
    await sync_to_async(cache.set)(cache_key, payload, timeout=60)
    return payload


@extend_schema(
    tags=["Stats"],
    summary="Get blog statistics with external data",
    description=(
        "Returns local blog counts together with exchange rates and current time in Almaty. "
        "Authentication is not required. "
        "The external HTTP calls are executed concurrently via asyncio.gather and httpx.AsyncClient."
    ),
    responses={
        200: OpenApiResponse(
            response=StatsResponseSerializer,
            description="Combined blog statistics and external public API data.",
        ),
        503: OpenApiResponse(
            response=StatsErrorSerializer,
            description="External API request failed.",
        ),
    },
    examples=[
        OpenApiExample(
            "Stats response",
            value={
                "blog": {
                    "total_posts": 42,
                    "total_comments": 137,
                    "total_users": 15,
                },
                "exchange_rates": {
                    "KZT": 450.23,
                    "RUB": 89.10,
                    "EUR": 0.92,
                },
                "current_time": "2024-03-15T18:30:00+05:00",
            },
            response_only=True,
        ),
    ],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def stats_view(request):
    try:
        payload = async_to_sync(build_stats_payload)()
        return Response(payload, status=status.HTTP_200_OK)
    except (httpx.HTTPError, KeyError, ValueError):
        return Response(
            {"detail": "Failed to fetch external data."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )