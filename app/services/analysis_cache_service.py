import json
from typing import Optional

from app.services.cache_keys import CacheKeys


class AnalysisCacheService:
    def __init__(self, redis_client, ttl_seconds: int = 60 * 60 * 24 * 30) -> None:
        """Create an analysis cache helper using Redis-compatible storage."""
        self.redis = redis_client
        self.ttl_seconds = ttl_seconds

    def get_by_sha256(self, image_sha256: str) -> Optional[dict]:
        """Read a cached analysis result by image SHA256."""
        raw_value = self.redis.get(CacheKeys.analysis_by_sha256(image_sha256))
        if not raw_value:
            return None
        return json.loads(raw_value)

    def set_by_sha256(self, image_sha256: str, analysis_result: dict) -> None:
        """Cache a public analysis result by image SHA256."""
        self.redis.setex(
            CacheKeys.analysis_by_sha256(image_sha256),
            self.ttl_seconds,
            json.dumps(analysis_result, ensure_ascii=False),
        )

    def get_guest_recent_analysis_id(self, guest_id: str) -> Optional[str]:
        """Return the most recent analysis id for a guest identity."""
        return self.redis.get(CacheKeys.guest_recent_analysis(guest_id))

    def set_guest_recent_analysis_id(self, guest_id: str, analysis_id: str) -> None:
        """Store the most recent analysis id for a guest identity."""
        self.redis.set(CacheKeys.guest_recent_analysis(guest_id), analysis_id)
