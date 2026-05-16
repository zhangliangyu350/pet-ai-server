from datetime import date


class CacheKeys:
    @staticmethod
    def analysis_by_sha256(image_sha256: str) -> str:
        """构造按图片 SHA256 存储分析结果的缓存 key。"""
        return f"analysis:sha256:{image_sha256}"

    @staticmethod
    def daily_analysis_count(identity: str, day: date) -> str:
        """构造指定身份和日期的每日配额计数 key。"""
        return f"analysis:daily:{identity}:{day.strftime('%Y%m%d')}"

    @staticmethod
    def last_analysis_at(identity: str) -> str:
        """构造存储身份最近分析时间戳的 key。"""
        return f"analysis:last:{identity}"

    @staticmethod
    def guest_recent_analysis(guest_id: str) -> str:
        """构造存储游客最近分析 ID 的 key。"""
        return f"guest:recent:{guest_id}"

    @staticmethod
    def session(token: str) -> str:
        """构造存储登录用户会话的 key。"""
        return f"session:{token}"


def user_identity(user_id: str) -> str:
    """返回登录用户的限流身份字符串。"""
    return f"user:{user_id}"


def guest_identity(guest_id: str) -> str:
    """返回游客用户的限流身份字符串。"""
    return f"guest:{guest_id}"
