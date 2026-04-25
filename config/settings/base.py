import os
from datetime import timedelta
from pathlib import Path

from decouple import config
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY")


def _parse_debug_flag(raw_value: str) -> bool:
    return str(raw_value).strip().lower() in {"1", "true", "t", "yes", "y", "on", "debug"}


DEBUG = _parse_debug_flag(config("DEBUG", default="false"))
APP_ENV = config("APP_ENV", default="development").strip().lower()
IS_PRODUCTION = APP_ENV in {"prod", "production"}


def _validate_secret_key(secret_key: str) -> None:
    normalized = (secret_key or "").strip()
    if not normalized or len(normalized) < 50:
        raise ImproperlyConfigured("SECRET_KEY must be set to a strong value.")
    if len(set(normalized)) < 5:
        raise ImproperlyConfigured("SECRET_KEY must include sufficient entropy.")
    if normalized.startswith("django-insecure-"):
        raise ImproperlyConfigured("SECRET_KEY must not use the auto-generated insecure development value.")


if IS_PRODUCTION:
    if DEBUG:
        raise ImproperlyConfigured("DEBUG must be disabled in production.")
    _validate_secret_key(SECRET_KEY)

_allowed_hosts = config("ALLOWED_HOSTS", default="")
if _allowed_hosts:
    ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts.split(",") if host.strip()]
elif DEBUG:
    ALLOWED_HOSTS = ["*"]
else:
    raise ImproperlyConfigured("ALLOWED_HOSTS must be set in production.")

if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS cannot be empty.")

if "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("Wildcard ALLOWED_HOSTS is not allowed. Set explicit hostnames.")

INSTALLED_APPS = [
    "daphne",
    "channels",
    "core.apps.CoreConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "django_celery_beat",
    "apps.auths.apps.AuthsConfig",
    "apps.profiles.apps.ProfilesConfig",
    "apps.social_auth.apps.SocialAuthConfig",
    "apps.notifications.apps.NotificationsConfig",
    "apps.managements.apps.ManagementsConfig",
    "apps.sales_team.apps.SalesTeamConfig",
    "apps.admin_dashboard.apps.AdminDashboardConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "core.middleware.request_id.RequestIdMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

def _build_database_settings() -> dict:
    engine = config("DB_ENGINE", default=config("ENGINE", default="")).strip()
    if not engine:
        raise ImproperlyConfigured("Database engine is missing. Set DB_ENGINE (or ENGINE).")

    if engine == "django.db.backends.sqlite3":
        sqlite_name = config("DB_NAME", default=config("NAME", default="db.sqlite3")).strip()
        if not sqlite_name:
            raise ImproperlyConfigured("DB_NAME (or NAME) must be provided for SQLite.")
        sqlite_path = Path(sqlite_name)
        if not sqlite_path.is_absolute():
            sqlite_path = BASE_DIR / sqlite_path
        return {
            "ENGINE": engine,
            "NAME": str(sqlite_path),
        }

    name = config("DB_NAME", default=config("NAME", default="")).strip()
    user = config("DB_USER", default=config("USER", default="")).strip()
    password = config("DB_PASSWORD", default=config("PASSWORD", default="")).strip()
    host = config("DB_HOST", default=config("HOST", default="")).strip()
    port = config("DB_PORT", default=config("PORT", default="")).strip()

    if not all([name, user, password, host, port]):
        raise ImproperlyConfigured(
            "For non-SQLite databases, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, and DB_PORT must all be set."
        )

    return {
        "ENGINE": engine,
        "NAME": name,
        "USER": user,
        "PASSWORD": password,
        "HOST": host,
        "PORT": port,
        "CONN_MAX_AGE": config("DB_CONN_MAX_AGE", default=60, cast=int),
    }


DATABASES = {"default": _build_database_settings()}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "EXCEPTION_HANDLER": "core.exception_handler.custom_exception_handler",
    "DEFAULT_THROTTLE_RATES": {
        "user": "60/min",
        "anon": "5/min",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=3600),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=15),
    "ALGORITHM": "HS256",
}

AUTH_USER_MODEL = "auths.CustomUser"
GOOGLE_OAUTH_CLIENT_ID = config("GOOGLE_OAUTH_CLIENT_ID", default="").strip()
_google_oauth_client_ids_raw = config("GOOGLE_OAUTH_CLIENT_IDS", default="").strip()
GOOGLE_OAUTH_CLIENT_IDS = [client_id.strip() for client_id in _google_oauth_client_ids_raw.split(",") if client_id.strip()]
if GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_ID not in GOOGLE_OAUTH_CLIENT_IDS:
    GOOGLE_OAUTH_CLIENT_IDS.append(GOOGLE_OAUTH_CLIENT_ID)
if IS_PRODUCTION and not GOOGLE_OAUTH_CLIENT_IDS:
    raise ImproperlyConfigured(
        "At least one Google OAuth client ID must be configured via GOOGLE_OAUTH_CLIENT_ID or GOOGLE_OAUTH_CLIENT_IDS."
    )

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = []
for static_dir in [os.path.join(BASE_DIR, "public/static"), os.path.join(BASE_DIR, "static")]:
    if os.path.isdir(static_dir):
        STATICFILES_DIRS.append(static_dir)

MEDIA_ROOT = os.path.join(BASE_DIR, "public/static")
MEDIA_URL = "api/v1/media/"

EMAIL_BACKEND = config("EMAIL_BACKEND")
EMAIL_HOST = config("EMAIL_HOST")
EMAIL_PORT = config("EMAIL_PORT")
EMAIL_USE_TLS = config("EMAIL_USE_TLS")
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL")

CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://127.0.0.1:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"

CHANNEL_REDIS_URL = config("CHANNEL_REDIS_URL", default="redis://127.0.0.1:6379/0")
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [CHANNEL_REDIS_URL]},
    },
}

WS_MESSAGE_RATE_LIMIT = config("WS_MESSAGE_RATE_LIMIT", cast=int, default=60)
WS_MESSAGE_RATE_WINDOW_SECONDS = config("WS_MESSAGE_RATE_WINDOW_SECONDS", cast=int, default=60)

ONESIGNAL_APP_ID = config("ONESIGNAL_APP_ID", default="")
ONESIGNAL_API_KEY = config("ONESIGNAL_API_KEY", default="")

CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

MIGRATION_MODULES = {
    "auths": "db.migrations.auths",
    "notifications": "db.migrations.notifications",
    "profiles": "db.migrations.profiles",
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_id": {
            "()": "core.logging.RequestIdFilter",
        }
    },
    "formatters": {
        "json": {
            "()": "core.logging.JsonFormatter",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["request_id"],
            "formatter": "json",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
