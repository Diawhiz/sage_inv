"""Authenticate WebSocket connections using a DRF token from the query string."""
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def get_user_from_token(token_key):
    from rest_framework.authtoken.models import Token
    try:
        return Token.objects.select_related('user').get(key=token_key).user
    except Token.DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware:
    """ASGI middleware that resolves ``?token=<key>`` into scope['user']."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get('query_string', b'').decode())
        token = query.get('token', [None])[0]
        scope['user'] = await get_user_from_token(token) if token else AnonymousUser()
        return await self.app(scope, receive, send)
