from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit

from minio import Minio
from minio.error import S3Error

from app.core.config import Settings, get_settings
from app.core.exceptions import BusinessError, ErrorCode


class StorageService:
    def __init__(self, settings: Settings = None, minio_client=None) -> None:
        """创建图片存储服务，按配置选择本地或 MinIO 存储。"""
        self.settings = settings or get_settings()
        self.minio_client = minio_client

    def save_image(self, image_id: str, image_type: str, content: bytes) -> str:
        """保存图片内容并返回可给前端和 AI 使用的访问地址。"""
        if self.settings.upload_storage == "local":
            return self._save_local_image(image_id=image_id, image_type=image_type, content=content)
        if self.settings.upload_storage == "minio":
            return self._save_minio_image(image_id=image_id, image_type=image_type, content=content)
        raise BusinessError(ErrorCode.upload_failed)

    def _save_local_image(self, image_id: str, image_type: str, content: bytes) -> str:
        """将图片字节写入本地开发目录，并返回公开访问地址。"""
        upload_dir = Path(self.settings.upload_local_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{image_id}.{image_type}"
        target_path = upload_dir / filename
        target_path.write_bytes(content)
        return f"{self.settings.public_image_base_url.rstrip('/')}/{filename}"

    def _save_minio_image(self, image_id: str, image_type: str, content: bytes) -> str:
        """将图片字节上传到 MinIO，并返回公开或代理访问地址。"""
        object_name = f"images/{image_id}.{image_type}"
        content_type = "image/png" if image_type == "png" else "image/jpeg"
        client = self._get_minio_client()

        try:
            if not client.bucket_exists(self.settings.minio_bucket):
                client.make_bucket(self.settings.minio_bucket)
            client.put_object(
                bucket_name=self.settings.minio_bucket,
                object_name=object_name,
                data=BytesIO(content),
                length=len(content),
                content_type=content_type,
            )
        except S3Error:
            raise BusinessError(ErrorCode.upload_failed) from None

        return f"{self.settings.public_image_base_url.rstrip('/')}/{object_name}"

    def _get_minio_client(self):
        """返回 MinIO 客户端，允许测试时注入假客户端。"""
        if self.minio_client is not None:
            return self.minio_client
        if not self.settings.minio_endpoint or not self.settings.minio_access_key:
            raise BusinessError(ErrorCode.upload_failed)
        endpoint, secure = self._normalize_minio_endpoint(self.settings.minio_endpoint)
        return Minio(
            endpoint=endpoint,
            access_key=self.settings.minio_access_key,
            secret_key=self.settings.minio_secret_key,
            secure=self.settings.minio_secure if secure is None else secure,
        )

    @staticmethod
    def _normalize_minio_endpoint(endpoint: str) -> tuple[str, bool]:
        """规范化 MinIO endpoint，兼容带 http/https 协议的配置。"""
        parsed = urlsplit(endpoint)
        if parsed.scheme in {"http", "https"}:
            return parsed.netloc, parsed.scheme == "https"
        return endpoint, None
