# Python modules
from typing import Any 

# Django modules
from django.db.models import Model, ForeignKey, BooleanField, DateTimeField, CASCADE

# Project modules
from apps.users.models import CustomUser
from apps.blogs.models import Comment

class Notification(Model):
    recipient = ForeignKey(
        CustomUser,
        on_delete=CASCADE,
    )

    comment = ForeignKey(
        Comment,
        on_delete=CASCADE,
    )

    is_read = BooleanField(
        default=False
    )

    created_at = DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient} — comment {self.comment_id}"