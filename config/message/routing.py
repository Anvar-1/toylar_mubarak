from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^msg/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/call/(?P<room_name>\w+)/$', consumers.CallConsumer.as_asgi()),  # Call
    re_path(r'^call/(?P<room_name>\w+)/$', consumers.CallConsumer.as_asgi()),
    re_path(r'^msg/$', consumers.ChatConsumer.as_asgi()),
]

