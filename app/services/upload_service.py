import uuid

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import BusinessError, ErrorCode
from app.models.image_asset import ImageAsset
from app.repositories.image_repository import ImageRepository
from app.schemas.upload import UploadImageResult
from app.services.storage_service import StorageService
from app.utils.hashing import sha256_bytes
from app.utils.image import validate_image


class UploadService:
    def __init__(
        self,
        db: Session,
        settings: Settings = None,
        storage_service: StorageService = None,
    ) -> None:
        """创建带数据库访问和存储配置的上传服务。"""
        self.db = db
        self.settings = settings or get_settings()
        self.image_repository = ImageRepository(db)
        self.storage_service = storage_service or StorageService(self.settings)

    def upload_image(self, content: bytes, pet_type: str = None) -> UploadImageResult:
        """校验、生成指纹、存储并持久化上传的宠物图片。"""
        if pet_type and pet_type not in {"cat", "dog"}:
            raise BusinessError(ErrorCode.validation_error)

        image_info = validate_image(content)
        image_sha256 = sha256_bytes(content)
        existing = self.image_repository.get_by_sha256(image_sha256)
        if existing is not None:
            return self._to_result(existing)

        image_id = self._new_image_id()
        image_url = self.storage_service.save_image(
            image_id=image_id,
            image_type=image_info.image_type,
            content=content,
        )
        image = ImageAsset(
            id=image_id,
            image_url=image_url,
            image_sha256=image_sha256,
            width=image_info.width,
            height=image_info.height,
            size=image_info.size,
        )
        self.image_repository.create(image)
        self.db.commit()
        return self._to_result(image)

    @staticmethod
    def _to_result(image: ImageAsset) -> UploadImageResult:
        """将图片模型转换为前端上传响应结构。"""
        return UploadImageResult(
            image_url=image.image_url,
            image_sha256=image.image_sha256,
            width=image.width,
            height=image.height,
            size=image.size,
        )

    @staticmethod
    def _new_image_id() -> str:
        """生成用于存储和数据库的不透明图片 ID。"""
        return f"image_{uuid.uuid4().hex}"
