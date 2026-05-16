from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.image_asset import ImageAsset


class ImageRepository:
    def __init__(self, db: Session) -> None:
        """创建绑定到数据库会话的图片仓储。"""
        self.db = db

    def get_by_id(self, image_id: str) -> Optional[ImageAsset]:
        """按主键返回图片资源。"""
        return self.db.get(ImageAsset, image_id)

    def get_by_sha256(self, image_sha256: str) -> Optional[ImageAsset]:
        """按 SHA256 指纹返回匹配的图片资源。"""
        statement = select(ImageAsset).where(ImageAsset.image_sha256 == image_sha256)
        return self.db.execute(statement).scalar_one_or_none()

    def create(self, image: ImageAsset) -> ImageAsset:
        """在当前事务中持久化新的图片资源。"""
        self.db.add(image)
        self.db.flush()
        return image
