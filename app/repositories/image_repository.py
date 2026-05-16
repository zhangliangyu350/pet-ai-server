from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.image_asset import ImageAsset


class ImageRepository:
    def __init__(self, db: Session) -> None:
        """Create an image repository bound to a database session."""
        self.db = db

    def get_by_id(self, image_id: str) -> Optional[ImageAsset]:
        """Return an image asset by primary key."""
        return self.db.get(ImageAsset, image_id)

    def get_by_sha256(self, image_sha256: str) -> Optional[ImageAsset]:
        """Return an image asset matching a SHA256 fingerprint."""
        statement = select(ImageAsset).where(ImageAsset.image_sha256 == image_sha256)
        return self.db.execute(statement).scalar_one_or_none()

    def create(self, image: ImageAsset) -> ImageAsset:
        """Persist a new image asset in the current transaction."""
        self.db.add(image)
        self.db.flush()
        return image
