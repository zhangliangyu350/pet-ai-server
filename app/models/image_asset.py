from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ImageAsset(TimestampMixin, Base):
    __tablename__ = "image_assets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    image_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    image_sha256: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)

