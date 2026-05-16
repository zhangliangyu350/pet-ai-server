import json
from typing import Optional

from app.services.cache_keys import CacheKeys


class AnalysisCacheService:
    def __init__(self, redis_client, ttl_seconds: int = 60 * 60 * 24 * 30) -> None:
        """创建使用 Redis 兼容存储的分析缓存助手。"""
        self.redis = redis_client
        self.ttl_seconds = ttl_seconds

    def get_by_sha256(self, image_sha256: str) -> Optional[dict]:
        """按图片 SHA256 读取缓存的分析结果。"""
        raw_value = self.redis.get(CacheKeys.analysis_by_sha256(image_sha256))
        if not raw_value:
            return None
        return json.loads(raw_value)

    def set_by_sha256(self, image_sha256: str, analysis_result: dict) -> None:
        """按图片 SHA256 缓存公开分析结果。"""
        self.redis.setex(
            CacheKeys.analysis_by_sha256(image_sha256),
            self.ttl_seconds,
            json.dumps(analysis_result, ensure_ascii=False),
        )

    def get_guest_recent_analysis_id(self, guest_id: str) -> Optional[str]:
        """返回游客身份最近一次分析 ID。"""
        return self.redis.get(CacheKeys.guest_recent_analysis(guest_id))

    def set_guest_recent_analysis_id(self, guest_id: str, analysis_id: str) -> None:
        """存储游客身份最近一次分析 ID。"""
        self.redis.set(CacheKeys.guest_recent_analysis(guest_id), analysis_id)
