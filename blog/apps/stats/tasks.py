# Python modules
import logging
from datetime import timedelta

# Django modules
from django.utils import timezone

# Third-party modules
from celery import shared_task

logger = logging.getLogger('stats')


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def generate_daily_stats() -> None:
    """Log counts of new posts, comments, and users in the last 24 hours."""
    from apps.blogs.models import Post, Comment
    from django.contrib.auth import get_user_model

    User = get_user_model()
    since = timezone.now() - timedelta(hours=24)

    new_posts    = Post.objects.filter(created_at__gte=since).count()
    new_comments = Comment.objects.filter(created_at__gte=since).count()
    new_users    = User.objects.filter(date_joined__gte=since).count()

    logger.info(
        'Daily stats — posts: %d, comments: %d, users: %d',
        new_posts, new_comments, new_users,
    )