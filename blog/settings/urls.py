# Django modules
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (SpectacularAPIView,
                                   SpectacularSwaggerView,
                                   SpectacularRedocView)

# Project modules
from apps.stats.views import stats_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', view=include("apps.users.urls")),
    path('api/', view=include("apps.blogs.urls")),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/stats/', stats_view, name = 'stats')
]
