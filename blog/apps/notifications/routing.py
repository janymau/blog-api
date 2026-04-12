# Python modules
from typing import Any

# Django AND Rest Framework modules
from django.urls import path

# Project modules
from apps.notifications.consumers import CommentConsumer

websocket_patterns = [
    path("ws/posts/<slug>/comments/", CommentConsumer.as_asgi())
]