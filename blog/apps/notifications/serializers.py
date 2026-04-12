# Django modules
from rest_framework.serializers import ModelSerializer, CharField, EmailField

# Project modules
from apps.notifications.models import Notification


class NotificationSerializer(ModelSerializer):
    comment_body   = CharField(source='comment.body', read_only=True)
    post_slug      = CharField(source='comment.post.slug', read_only=True)
    commenter_email = EmailField(source='comment.author.email', read_only=True)

    class Meta:
        model  = Notification
        fields = ['id', 'comment_body', 'post_slug', 'commenter_email', 'is_read', 'created_at']