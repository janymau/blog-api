# Python modules
import json
from typing import Any

# Django modules
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

# Redis
import redis

# Project modules
from apps.blogs.models import Comment, Post
from apps.notifications.models import Notification
from settings.base import REDIS_URL
from apps.blogs.tasks import invalidate_posts_cache

SSE_CHANNEL = "posts:published"

_redis = redis.from_url(REDIS_URL)

@receiver(post_save, sender=Post)
def publish_post_event(sender, instance : Post, created : bool, **kwargs : dict[str, Any]):
    if instance.status != 'published':
        return
    
    if not created:
        try:
            previous = Post.objects.get(pk = instance.pk)
        except Post.DoesNotExist:
            return
    
    payload = json.dumps(
        {
            "post_id" : str(instance.pk),
            "title" : instance.title,
            "slug" : instance.slug,
            "author" : {
                "id" : str(instance.author.id),
                "email" : instance.author.email,
            },
            "published_at" : instance.created_at.isoformat() if instance.created_at else None
        }

    )

    _redis.publish(SSE_CHANNEL, payload)

@receiver(post_save, sender=Comment)
def create_notification(sender, instance: Comment, created: bool, **kwargs):
    """Create a Notification for the post author when a new comment is posted."""
    if not created:
        return

    post_author = instance.post.author

    if instance.author == post_author:
        return

    from apps.notifications.models import Notification
    Notification.objects.create(
        recipient=post_author,
        comment=instance,
    )


@receiver(post_save, sender=Post)
def on_post_save(sender, instance, **kwargs):
    invalidate_posts_cache.delay()

@receiver(post_delete, sender=Post)
def on_post_delete(sender, instance, **kwargs):
    invalidate_posts_cache.delay()