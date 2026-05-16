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
        """创建基于 Redis 类计数器的分析限流器。"""
        self.redis = redis_client
        self.guest_daily_limit = guest_daily_limit
        self.user_daily_limit = user_daily_limit
        self.interval_seconds = interval_seconds

    def check_and_consume(self, identity: str, is_guest: bool, now: datetime = None) -> None:
        """校验请求间隔和每日配额，并消耗一次分析次数。"""
        current_time = now or datetime.utcnow()
        self._check_interval(identity, current_time)
        self._consume_daily_count(identity, is_guest, current_time.date())
        self.redis.set(CacheKeys.last_analysis_at(identity), str(int(current_time.timestamp())))

    def _check_interval(self, identity: str, current_time: datetime) -> None:
        """当身份提交分析过于频繁时抛出业务异常。"""
        key = CacheKeys.last_analysis_at(identity)
        last_timestamp = self.redis.get(key)
        if not last_timestamp:
            return

        elapsed = current_time.timestamp() - int(last_timestamp)
        if elapsed < self.interval_seconds:
            raise BusinessError(ErrorCode.analysis_too_frequent)

    def _consume_daily_count(self, identity: str, is_guest: bool, day: date) -> None:
        """递增每日分析次数，并执行游客/用户配额限制。"""
        limit = self.guest_daily_limit if is_guest else self.user_daily_limit
        key = CacheKeys.daily_analysis_count(identity, day)
        count = self.redis.incr(key)

        if count == 1:
            self.redis.expireat(key, self._next_day_timestamp(day))

        if count > limit:
            raise BusinessError(ErrorCode.analysis_limit_exceeded)

    @staticmethod
    def _next_day_timestamp(day: date) -> int:
        """返回下一天零点的 Unix 时间戳。"""
        next_day = datetime.combine(day + timedelta(days=1), datetime.min.time())
        return int(next_day.timestamp())
