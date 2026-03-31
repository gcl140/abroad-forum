from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/replies-counts/$', consumers.RepliesCountConsumer.as_asgi()),
]
