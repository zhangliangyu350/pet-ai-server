from functools import lru_cache

from redis import Redis

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_redis_client() -> Redis:
    """Return a cached Redis client configured from the current settings."""
    return Redis.from_url(get_settings().redis_url, decode_responses=True)
