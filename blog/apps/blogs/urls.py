# Django modules
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Project modules
from apps.blogs.views import PostViewSet


router : DefaultRouter = DefaultRouter(
    trailing_slash = False
)

router.register(
    prefix="posts",
    viewset=PostViewSet,
    basename='post'
)

urlpatterns = [
    path("", include(router.urls))
]
