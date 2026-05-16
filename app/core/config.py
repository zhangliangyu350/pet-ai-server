from dataclasses import dataclass
from functools import lru_cache
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_env: str = "development"
    app_name: str = "Pet AI Server"
    app_secret: str = "change_me"
    database_url: str = "mysql+pymysql://user:password@localhost:3306/pet_ai"
    redis_url: str = "redis://localhost:6379/0"
    wechat_app_id: str = ""
    wechat_app_secret: str = ""
    ai_provider: str = "deepseek"
    ai_api_key: str = ""
    ai_api_base_url: str = ""
    upload_storage: str = "local"
    upload_local_dir: str = "./storage/uploads"
    public_image_base_url: str = "http://localhost:8000/static/uploads"
    minio_endpoint: str = "127.0.0.1:9000"
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket: str = "pet-ai-images"
    minio_secure: bool = False


def _read_env(name: str, default: str) -> str:
    """读取环境变量，并在未设置时保留默认值。"""
    value = os.getenv(name)
    return value if value is not None else default


def _read_bool_env(name: str, default: bool) -> bool:
    """读取布尔环境变量，并支持常见 true/false 字符串。"""
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """返回从环境变量加载并缓存的应用配置。"""
    return Settings(
        app_env=_read_env("APP_ENV", Settings.app_env),
        app_name=_read_env("APP_NAME", Settings.app_name),
        app_secret=_read_env("APP_SECRET", Settings.app_secret),
        database_url=_read_env("DATABASE_URL", Settings.database_url),
        redis_url=_read_env("REDIS_URL", Settings.redis_url),
        wechat_app_id=_read_env("WECHAT_APP_ID", Settings.wechat_app_id),
        wechat_app_secret=_read_env("WECHAT_APP_SECRET", Settings.wechat_app_secret),
        ai_provider=_read_env("AI_PROVIDER", Settings.ai_provider),
        ai_api_key=_read_env("AI_API_KEY", Settings.ai_api_key),
        ai_api_base_url=_read_env("AI_API_BASE_URL", Settings.ai_api_base_url),
        upload_storage=_read_env("UPLOAD_STORAGE", Settings.upload_storage),
        upload_local_dir=_read_env("UPLOAD_LOCAL_DIR", Settings.upload_local_dir),
        public_image_base_url=_read_env(
            "PUBLIC_IMAGE_BASE_URL",
            Settings.public_image_base_url,
        ),
        minio_endpoint=_read_env("MINIO_ENDPOINT", Settings.minio_endpoint),
        minio_access_key=_read_env("MINIO_ACCESS_KEY", Settings.minio_access_key),
        minio_secret_key=_read_env("MINIO_SECRET_KEY", Settings.minio_secret_key),
        minio_bucket=_read_env("MINIO_BUCKET", Settings.minio_bucket),
        minio_secure=_read_bool_env("MINIO_SECURE", Settings.minio_secure),
    )
