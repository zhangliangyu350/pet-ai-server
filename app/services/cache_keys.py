from datetime import date


class CacheKeys:
    @staticmethod
    def analysis_by_sha256(image_sha256: str) -> str:
        return f"analysis:sha256:{image_sha256}"

    @staticmethod
    def daily_analysis_count(identity: str, day: date) -> str:
        return f"analysis:daily:{identity}:{day.strftime('%Y%m%d')}"

    @staticmethod
    def last_analysis_at(identity: str) -> str:
        return f"analysis:last:{identity}"

    @staticmethod
    def guest_recent_analysis(guest_id: str) -> str:
        return f"guest:recent:{guest_id}"

    @staticmethod
    def session(token: str) -> str:
        return f"session:{token}"


def user_identity(user_id: str) -> str:
    return f"user:{user_id}"


def guest_identity(guest_id: str) -> str:
    return f"guest:{guest_id}"

