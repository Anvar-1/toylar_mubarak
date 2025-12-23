import os
from urllib.parse import parse_qs
from channels.db import database_sync_to_async

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken, TokenError

User = get_user_model()

@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()

class WebSocketJWTAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # ✅ query_string bytes → str
        query_string = scope["query_string"].decode()
        parsed_query_string = parse_qs(query_string)
        token = parsed_query_string.get("token", [None])[0]  # ✅ endi str key

        if token:
            try:
                access_token = AccessToken(token)
                user_id = access_token["user_id"]
                scope["user"] = await get_user(user_id)
                print(f"✅ WebSocket connected: user_id={user_id}")
            except TokenError:
                print("❌ Invalid token")
                scope["user"] = AnonymousUser()
        else:
            print("⚠️ No token provided")
            scope["user"] = AnonymousUser()

        return await self.app(scope, receive, send)




