# Django modules
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Project modules
from apps.blogs.views import PostViewSet
from apps.notifications.sse import post_stream


router : DefaultRouter = DefaultRouter(
    trailing_slash = False
)

router.register(
    prefix="posts",
    viewset=PostViewSet,
    basename='post'
)

urlpatterns = [
    path("posts/stream/", post_stream, name='post-stream'),
    path("", include(router.urls)),
]


