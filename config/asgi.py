import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

from apps.chats.routing import websocket_urlpatterns as chat_websocket_urlpatterns
from apps.notifications.routing import websocket_urlpatterns as notification_websocket_urlpatterns
from core.auth_middleware import CustomAuthMiddleware

default_settings_module = (
    "config.settings.prod"
    if os.getenv("APP_ENV", "development").strip().lower() in {"prod", "production"}
    else "config.settings.dev"
)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", default_settings_module))

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AllowedHostsOriginValidator(
            CustomAuthMiddleware(URLRouter(chat_websocket_urlpatterns + notification_websocket_urlpatterns))
        ),
    }
)
