# Python modules
from typing import Any
import json

# Django and Rest Framework modules
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

# Project modules
from apps.blogs.models import Post

class CommentConsumer(AsyncWebsocketConsumer):
    """
        Comment Consumer for WebSocket
    """
    @database_sync_to_async
    def get_post(self, slug : str):
        try:
            return Post.objects.get(slug = slug, status = 'published')
        except Post.DoesNotExist:
            return None
        
    async def connect(self):
        from django.contrib.auth.models import AnonymousUser
        user = self.scope.get('user')

        if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
            await self.close(code=4001)
            return
        
        self.slug = self.scope['url_route']['kwargs']['slug']
        post = await self.get_post(self.slug)
        if post is None:
            await self.close(code=4004)
            return

        self.room_group_name = f"comment_{self.slug}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
    
    async def receive(self, text_data = None, bytes_data = None):
        data = json.loads(text_data)
        message = data.get('message')
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type" : "chat_message",
                "message" : message
            }

        )

    
    async def chat_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            "message" : message
        }))

    async def disconnect(self, code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
