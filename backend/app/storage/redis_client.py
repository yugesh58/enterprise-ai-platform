from functools import lru_cache

import redis

from app.core.config import settings


@lru_cache(maxsize=1)
def get_redis_client() -> redis.Redis:
    """Return a shared Redis client with a connection pool."""
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        socket_connect_timeout=2,
        socket_timeout=2,
        decode_responses=True,
    )