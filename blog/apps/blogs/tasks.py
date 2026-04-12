"""
Retry policy rationale:
Cache invalidation talks to Redis which can be momentarily unreachable.
A failed invalidation leaves stale data in the cache — retrying ensures
consistency without requiring the request cycle to wait.

publish_scheduled_posts must also retry: if the DB or Redis blips during
the beat window, skipping silently would leave scheduled posts stuck forever.
"""

# Python modules
import logging
import json

# Django modules
from django.utils import timezone

# Third-party modules
from celery import shared_task
import redis

# Project modules
from settings.base import REDIS_URL

logger = logging.getLogger('blogs')
SSE_CHANNEL = 'posts:published'
_redis = redis.from_url(REDIS_URL)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def invalidate_posts_cache() -> None:
    """Delete all cached post-list and post-detail keys from Redis."""
    client = redis.from_url(REDIS_URL)
    keys = client.keys('posts:*')
    if keys:
        client.delete(*keys)
    logger.info('Posts cache invalidated (%d keys removed)', len(keys))


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def publish_scheduled_posts() -> None:
    """Publish all posts whose publish_at <= now and status == scheduled."""
    from apps.blogs.models import Post

    now = timezone.now()
    posts = Post.objects.filter(status='scheduled', publish_at__lte=now)

    for post in posts:
        post.status = 'published'
        post.published_at = now
        post.save(update_fields=['status', 'published_at'])

        payload = json.dumps({
            'post_id':      str(post.id),
            'title':        post.title,
            'slug':         post.slug,
            'author':       {'id': str(post.author.id), 'email': post.author.email},
            'published_at': post.published_at.isoformat(),
        })
        _redis.publish(SSE_CHANNEL, payload)
        logger.info('Auto-published post: %s', post.slug)