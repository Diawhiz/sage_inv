"""
ASGI config for sage_inv project.

Routes HTTP to Django and WebSocket traffic through Channels with
token-based authentication.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sage_inv.settings')

# Initialise Django before importing anything that touches the app registry.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402
from core.routing import websocket_urlpatterns  # noqa: E402
from core.ws_auth import TokenAuthMiddleware  # noqa: E402

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        TokenAuthMiddleware(URLRouter(websocket_urlpatterns))
    ),
})
