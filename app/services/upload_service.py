from pathlib import Path
import uuid

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import BusinessError, ErrorCode
from app.models.image_asset import ImageAsset
from app.repositories.image_repository import ImageRepository
from app.schemas.upload import UploadImageResult
from app.utils.hashing import sha256_bytes
from app.utils.image import validate_image


class UploadService:
    def __init__(self, db: Session, settings: Settings = None) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.image_repository = ImageRepository(db)

    def upload_image(self, content: bytes, pet_type: str = None) -> UploadImageResult:
        if pet_type and pet_type not in {"cat", "dog"}:
            raise BusinessError(ErrorCode.validation_error)

        image_info = validate_image(content)
        image_sha256 = sha256_bytes(content)
        existing = self.image_repository.get_by_sha256(image_sha256)
        if existing is not None:
            return self._to_result(existing)

        image_id = self._new_image_id()
        image_url = self._save_local_image(
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

    def _save_local_image(self, image_id: str, image_type: str, content: bytes) -> str:
        if self.settings.upload_storage != "local":
            raise BusinessError(ErrorCode.upload_failed)

        upload_dir = Path(self.settings.upload_local_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{image_id}.{image_type}"
        target_path = upload_dir / filename
        target_path.write_bytes(content)
        return f"{self.settings.public_image_base_url.rstrip('/')}/{filename}"

    @staticmethod
    def _to_result(image: ImageAsset) -> UploadImageResult:
        return UploadImageResult(
            image_url=image.image_url,
            image_sha256=image.image_sha256,
            width=image.width,
            height=image.height,
            size=image.size,
        )

    @staticmethod
    def _new_image_id() -> str:
        return f"image_{uuid.uuid4().hex}"

