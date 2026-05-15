from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.image_asset import ImageAsset


class ImageRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, image_id: str) -> Optional[ImageAsset]:
        return self.db.get(ImageAsset, image_id)

    def get_by_sha256(self, image_sha256: str) -> Optional[ImageAsset]:
        statement = select(ImageAsset).where(ImageAsset.image_sha256 == image_sha256)
        return self.db.execute(statement).scalar_one_or_none()

    def create(self, image: ImageAsset) -> ImageAsset:
        self.db.add(image)
        self.db.flush()
        return image

