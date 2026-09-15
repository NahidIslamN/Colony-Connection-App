import os
from decouple import config

from django.core.wsgi import get_wsgi_application

default_settings_module = (
    "config.settings.prod"
    if config("APP_ENV", default="development").strip().lower() in {"prod", "production"}
    else "config.settings.dev"
)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", config("DJANGO_SETTINGS_MODULE", default=default_settings_module))

application = get_wsgi_application()
