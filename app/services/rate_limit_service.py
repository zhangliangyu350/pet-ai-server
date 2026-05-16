from datetime import date, datetime, timedelta

from app.core.exceptions import BusinessError, ErrorCode
from app.services.cache_keys import CacheKeys


class AnalysisRateLimitService:
    def __init__(
        self,
        redis_client,
        guest_daily_limit: int = 3,
        user_daily_limit: int = 10,
        interval_seconds: int = 10,
    ) -> None:
        """Create an analysis rate limiter backed by Redis-like counters."""
        self.redis = redis_client
        self.guest_daily_limit = guest_daily_limit
        self.user_daily_limit = user_daily_limit
        self.interval_seconds = interval_seconds

    def check_and_consume(self, identity: str, is_guest: bool, now: datetime = None) -> None:
        """Validate interval and daily quota, then consume one analysis attempt."""
        current_time = now or datetime.utcnow()
        self._check_interval(identity, current_time)
        self._consume_daily_count(identity, is_guest, current_time.date())
        self.redis.set(CacheKeys.last_analysis_at(identity), str(int(current_time.timestamp())))

    def _check_interval(self, identity: str, current_time: datetime) -> None:
        """Raise when an identity submits analyses more often than allowed."""
        key = CacheKeys.last_analysis_at(identity)
        last_timestamp = self.redis.get(key)
        if not last_timestamp:
            return

        elapsed = current_time.timestamp() - int(last_timestamp)
        if elapsed < self.interval_seconds:
            raise BusinessError(ErrorCode.analysis_too_frequent)

    def _consume_daily_count(self, identity: str, is_guest: bool, day: date) -> None:
        """Increment daily analysis count and enforce guest/user quota."""
        limit = self.guest_daily_limit if is_guest else self.user_daily_limit
        key = CacheKeys.daily_analysis_count(identity, day)
        count = self.redis.incr(key)

        if count == 1:
            self.redis.expireat(key, self._next_day_timestamp(day))

        if count > limit:
            raise BusinessError(ErrorCode.analysis_limit_exceeded)

    @staticmethod
    def _next_day_timestamp(day: date) -> int:
        """Return the Unix timestamp for the start of the next day."""
        next_day = datetime.combine(day + timedelta(days=1), datetime.min.time())
        return int(next_day.timestamp())
