import os

import redis
from django.conf import settings

REDIS_URL = getattr(settings, "CHANNEL_REDIS_URL", os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/1"))

try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
except (redis.RedisError, TypeError, ValueError):
    redis_client = None
