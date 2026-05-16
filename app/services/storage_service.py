from pathlib import Path
from urllib.parse import unquote, urlsplit

from app.core.config import Settings, get_settings
from app.core.exceptions import BusinessError, ErrorCode


class StorageService:
    def __init__(self, settings: Settings = None) -> None:
        """创建图片本地存储服务。"""
        self.settings = settings or get_settings()

    def save_image(self, image_id: str, image_type: str, content: bytes) -> str:
        """将图片字节写入本地开发目录，并返回前端访问地址。"""
        upload_dir = Path(self.settings.upload_local_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{image_id}.{image_type}"
        target_path = upload_dir / filename
        target_path.write_bytes(content)
        return f"{self.settings.public_image_base_url.rstrip('/')}/{filename}"

    def read_image(self, image_url: str) -> tuple[bytes, str]:
        """根据已保存的图片访问地址读取本地图片字节和图片类型。"""
        filename = self._filename_from_url(image_url)
        image_path = Path(self.settings.upload_local_dir) / filename
        if not image_path.is_file():
            raise BusinessError(ErrorCode.image_required)

        try:
            content = image_path.read_bytes()
        except OSError:
            raise BusinessError(ErrorCode.image_required) from None

        image_type = image_path.suffix.lower().lstrip(".")
        if image_type == "jpg":
            image_type = "jpeg"
        return content, image_type

    def _filename_from_url(self, image_url: str) -> str:
        """从公开图片 URL 中提取本地文件名，并拒绝跨目录路径。"""
        base_url = self.settings.public_image_base_url.rstrip("/")
        if not image_url.startswith(f"{base_url}/"):
            raise BusinessError(ErrorCode.image_required)

        parsed_path = unquote(urlsplit(image_url).path)
        filename = Path(parsed_path).name
        if not filename or filename in {".", ".."}:
            raise BusinessError(ErrorCode.image_required)
        return filename
