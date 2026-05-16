from functools import lru_cache

from redis import Redis

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_redis_client() -> Redis:
    """返回按当前配置创建并缓存的 Redis 客户端。"""
    return Redis.from_url(get_settings().redis_url, decode_responses=True)
