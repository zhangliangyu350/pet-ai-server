from datetime import date, datetime

import pytest

from app.core.exceptions import BusinessError, ErrorCode
from app.services.analysis_cache_service import AnalysisCacheService
from app.services.cache_keys import CacheKeys, guest_identity, user_identity
from app.services.rate_limit_service import AnalysisRateLimitService
from tests.fakes import FakeRedis


def test_cache_keys_match_contract():
    assert CacheKeys.analysis_by_sha256("abc") == "analysis:sha256:abc"
    assert CacheKeys.daily_analysis_count("user:user_001", date(2026, 5, 16)) == (
        "analysis:daily:user:user_001:20260516"
    )
    assert CacheKeys.last_analysis_at("guest:guest_001") == "analysis:last:guest:guest_001"
    assert CacheKeys.guest_recent_analysis("guest_001") == "guest:recent:guest_001"
    assert CacheKeys.session("token") == "session:token"
    assert user_identity("user_001") == "user:user_001"
    assert guest_identity("guest_001") == "guest:guest_001"


def test_analysis_cache_round_trips_by_sha256():
    redis = FakeRedis()
    service = AnalysisCacheService(redis_client=redis)

    service.set_by_sha256("sha256_001", {"id": "analysis_001", "riskLevel": "low"})

    assert service.get_by_sha256("sha256_001") == {
        "id": "analysis_001",
        "riskLevel": "low",
    }


def test_rate_limit_allows_within_limits():
    redis = FakeRedis()
    service = AnalysisRateLimitService(redis_client=redis)

    service.check_and_consume(
        identity="guest:guest_001",
        is_guest=True,
        now=datetime(2026, 5, 16, 10, 0, 0),
    )

    assert redis.get("analysis:daily:guest:guest_001:20260516") == "1"


def test_rate_limit_blocks_too_frequent_requests():
    redis = FakeRedis()
    service = AnalysisRateLimitService(redis_client=redis)
    service.check_and_consume(
        identity="guest:guest_001",
        is_guest=True,
        now=datetime(2026, 5, 16, 10, 0, 0),
    )

    with pytest.raises(BusinessError) as exc_info:
        service.check_and_consume(
            identity="guest:guest_001",
            is_guest=True,
            now=datetime(2026, 5, 16, 10, 0, 5),
        )

    assert exc_info.value.code == ErrorCode.analysis_too_frequent


def test_rate_limit_blocks_guest_daily_limit():
    redis = FakeRedis()
    service = AnalysisRateLimitService(redis_client=redis, interval_seconds=0)

    for index in range(3):
        service.check_and_consume(
            identity="guest:guest_001",
            is_guest=True,
            now=datetime(2026, 5, 16, 10, index, 0),
        )

    with pytest.raises(BusinessError) as exc_info:
        service.check_and_consume(
            identity="guest:guest_001",
            is_guest=True,
            now=datetime(2026, 5, 16, 10, 4, 0),
        )

    assert exc_info.value.code == ErrorCode.analysis_limit_exceeded

