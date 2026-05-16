from datetime import date


class CacheKeys:
    @staticmethod
    def analysis_by_sha256(image_sha256: str) -> str:
        """Build the cache key for an analysis result by image SHA256."""
        return f"analysis:sha256:{image_sha256}"

    @staticmethod
    def daily_analysis_count(identity: str, day: date) -> str:
        """Build the daily quota counter key for an identity and date."""
        return f"analysis:daily:{identity}:{day.strftime('%Y%m%d')}"

    @staticmethod
    def last_analysis_at(identity: str) -> str:
        """Build the key storing the last analysis timestamp for an identity."""
        return f"analysis:last:{identity}"

    @staticmethod
    def guest_recent_analysis(guest_id: str) -> str:
        """Build the key storing a guest user's most recent analysis id."""
        return f"guest:recent:{guest_id}"

    @staticmethod
    def session(token: str) -> str:
        """Build the key storing an authenticated user session."""
        return f"session:{token}"


def user_identity(user_id: str) -> str:
    """Return the rate-limit identity string for a logged-in user."""
    return f"user:{user_id}"


def guest_identity(guest_id: str) -> str:
    """Return the rate-limit identity string for a guest user."""
    return f"guest:{guest_id}"
