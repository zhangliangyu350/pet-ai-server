import logging
import re


SENSITIVE_PATTERNS = (
    re.compile(r"(?i)(appid=)[^&\s]+"),
    re.compile(r"(?i)(secret=)[^&\s]+"),
    re.compile(r"(?i)(js_code=)[^&\s]+"),
    re.compile(r"(?i)(access_token=)[^&\s]+"),
    re.compile(r"(?i)(api[_-]?key=)[^&\s]+"),
    re.compile(r"(?i)(password=)[^&\s]+"),
    re.compile(r"(?i)(token=)[^&\s]+"),
    re.compile(r"(?i)(authorization:\s*bearer\s+)[^\s]+"),
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/-]+"),
)


def mask_sensitive_text(value: str) -> str:
    """对日志文本中的密钥、token、code 等敏感字段做脱敏。"""
    masked = value
    for pattern in SENSITIVE_PATTERNS:
        masked = pattern.sub(r"\1***", masked)
    return masked


class SensitiveDataFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        """在日志输出前对消息和参数进行敏感信息脱敏。"""
        if isinstance(record.msg, str):
            record.msg = mask_sensitive_text(record.msg)

        if isinstance(record.args, dict):
            record.args = {
                key: mask_sensitive_text(str(value)) for key, value in record.args.items()
            }
        elif isinstance(record.args, tuple):
            record.args = tuple(mask_sensitive_text(str(value)) for value in record.args)

        return True


def configure_logging(app_env: str) -> None:
    """配置根日志级别并安装敏感数据过滤器。"""
    level = logging.DEBUG if app_env == "development" else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    sensitive_filter = SensitiveDataFilter()
    root_logger = logging.getLogger()
    root_logger.addFilter(sensitive_filter)
    for handler in root_logger.handlers:
        handler.addFilter(sensitive_filter)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
