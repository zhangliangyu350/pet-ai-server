import logging


class SensitiveDataFilter(logging.Filter):
    blocked_words = ("token", "secret", "password", "api_key", "authorization")

    def filter(self, record: logging.LogRecord) -> bool:
        """Drop log records that appear to contain sensitive credential fields."""
        message = record.getMessage().lower()
        return not any(word in message for word in self.blocked_words)


def configure_logging(app_env: str) -> None:
    """Configure root logging verbosity and install the sensitive-data filter."""
    level = logging.DEBUG if app_env == "development" else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logging.getLogger().addFilter(SensitiveDataFilter())
