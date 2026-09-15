import os
from decouple import config

from django.core.asgi import get_asgi_application
import django

default_settings_module = (
    "config.settings.prod"
    if config("APP_ENV", default="development").strip().lower() in {"prod", "production"}
    else "config.settings.dev"
)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", config("DJANGO_SETTINGS_MODULE", default=default_settings_module))

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

from apps.notifications.routing import websocket_urlpatterns as notification_websocket_urlpatterns
from core.auth_middleware import CustomAuthMiddleware

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            CustomAuthMiddleware(URLRouter(notification_websocket_urlpatterns))
        ),
    }
)
