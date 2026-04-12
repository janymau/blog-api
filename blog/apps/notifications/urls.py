from django.urls import path
from apps.notifications.views import notification_count, notification_list, mark_all_read

urlpatterns = [
    path('notifications/',        notification_list,  name='notification-list'),
    path('notifications/count/',  notification_count, name='notification-count'),
    path('notifications/read/',   mark_all_read,      name='notification-read'),
]