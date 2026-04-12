"""
Retry policy rationale:
process_new_comment does two things: DB write (Notification) and Redis
publish (WebSocket fan-out). Either can fail transiently. Without retries
a network blip would silently drop both the notification and the real-time
message. Celery's idempotency + retries guarantee at-least-once delivery.

clear_expired_notifications is a bulk DELETE — if the DB is under load
and the query times out, a retry is cheaper than losing the cleanup window.
"""

# Python modules
import logging

# Django modules
from django.utils import timezone
from datetime import timedelta

# Third-party modules
from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger('notifications')


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def process_new_comment(comment_id: int) -> None:
    """
    Triggered on every new comment. Handles two side effects:
    1. Create a Notification for the post author.
    2. Publish the comment to the WebSocket channel group.
    """
    from apps.blogs.models import Comment
    from apps.notifications.models import Notification

    try:
        comment = Comment.objects.select_related(
            'post', 'post__author', 'author'
        ).get(id=comment_id)
    except Comment.DoesNotExist:
        logger.warning('process_new_comment: comment %d not found', comment_id)
        return

    post_author = comment.post.author

    if comment.author != post_author:
        Notification.objects.create(
            recipient=post_author,
            comment=comment,
        )

    channel_layer = get_channel_layer()
    group_name = f'comment_{comment.post.slug}'

    comment_data = {
        'comment_id': comment.id,
        'author':     {'id': comment.author.id, 'email': comment.author.email},
        'body':       comment.body,
        'created_at': comment.created_at.isoformat(),
    }

    async_to_sync(channel_layer.group_send)(
        group_name,
        {'type': 'chat_message', 'message': comment_data},
    )
    logger.info('Processed comment %d on post %s', comment_id, comment.post.slug)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def clear_expired_notifications() -> None:
    """Delete notifications older than 30 days."""
    from apps.notifications.models import Notification

    cutoff = timezone.now() - timedelta(days=30)
    deleted, _ = Notification.objects.filter(created_at__lt=cutoff).delete()
    logger.info('Cleared %d expired notifications', deleted)