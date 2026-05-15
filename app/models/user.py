from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.analysis import Analysis
    from app.models.health_record import HealthRecord


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    openid: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    nickname: Mapped[str] = mapped_column(String(64), default="微信用户", nullable=False)
    avatar_url: Mapped[str] = mapped_column(String(512), default="", nullable=False)

    analyses: Mapped[list["Analysis"]] = relationship(back_populates="user")
    records: Mapped[list["HealthRecord"]] = relationship(back_populates="user")
