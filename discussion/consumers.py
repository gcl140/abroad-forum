import json
from channels.generic.websocket import AsyncWebsocketConsumer

GROUP_NAME = 'reply_counts'


class RepliesCountConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(GROUP_NAME, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(GROUP_NAME, self.channel_name)

    async def receive(self, text_data):
        pass  # clients only listen, never send

    async def reply_count_update(self, event):
        await self.send(text_data=json.dumps({
            'post_id': event['post_id'],
            'count': event['count'],
        }))
