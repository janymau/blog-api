# Python modules
import os
import django


from settings.conf import ENV_ID, ENV_POSSIBLE_OPTIONS
assert ENV_ID in ENV_POSSIBLE_OPTIONS, f"Invalid env id. Possible options {ENV_POSSIBLE_OPTIONS}"
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'settings.env.{ENV_ID}')
django.setup()

# Django modules
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator


# Project modules
from apps.notifications.routing import websocket_patterns
from apps.core.middleware import JWTAuthUserMiddleware


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        JWTAuthUserMiddleware(
            URLRouter(websocket_patterns)
        )
    ),
})
