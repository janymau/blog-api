# Django modules
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Project modules
from apps.stats.views import stats_view

router : DefaultRouter = DefaultRouter(
    trailing_slash = False
)

router.register(
    prefix="stats",
    viewset=stats_view,
    basename='stat'
)

urlpatterns = [
    path("v2", include(router.urls))
]
