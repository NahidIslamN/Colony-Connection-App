import redis

from infrastructure.cache import redis_client


def should_enqueue_task(user_id: int) -> bool:
    key = f"delivered_task:{user_id}"
    try:
        if redis_client is None:
            return True

        if redis_client.exists(key):
            return False

        redis_client.set(key, "1", ex=60)
        return True
    except redis.RedisError:
        return True
