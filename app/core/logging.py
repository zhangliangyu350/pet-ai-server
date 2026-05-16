import logging


class SensitiveDataFilter(logging.Filter):
    blocked_words = ("token", "secret", "password", "api_key", "authorization")

    def filter(self, record: logging.LogRecord) -> bool:
        """丢弃疑似包含敏感凭证字段的日志记录。"""
        message = record.getMessage().lower()
        return not any(word in message for word in self.blocked_words)


def configure_logging(app_env: str) -> None:
    """配置根日志级别并安装敏感数据过滤器。"""
    level = logging.DEBUG if app_env == "development" else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logging.getLogger().addFilter(SensitiveDataFilter())
