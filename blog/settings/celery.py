# Python modules
import os
import django
from celery import Celery
from celery.schedules import crontab
from settings.conf import ENV_ID, ENV_POSSIBLE_OPTIONS
assert ENV_ID in ENV_POSSIBLE_OPTIONS, f"Invalid env id. Possible options {ENV_POSSIBLE_OPTIONS}"
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'settings.env.{ENV_ID}')
django.setup()

app = Celery('blog')
app.config_from_object('django.conf:settings', namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'publish-schedules-posts' : {
        'task' : 'apps.blogs.tasks.publish_scheduled_posts',
        'schedule' : 60.0
    },
    'clear_expired_notifications' : {
        'task' : 'apps.notifications.tasks.clear_expired_notifications',
        'schedule' : crontab(hour=3, minute=0)
    },
    'generate_daily_stats' : {
        'task': 'apps.stats.tasks.generate_daily_stats',
        'schedule': crontab(hour=0, minute=0),
    }

}
