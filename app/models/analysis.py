from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.health_record import HealthRecord
    from app.models.user import User


class Analysis(TimestampMixin, Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("users.id"),
        index=True,
        nullable=True,
    )
    guest_id: Mapped[Optional[str]] = mapped_column(String(128), index=True, nullable=True)
    image_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    image_sha256: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    pet_type: Mapped[str] = mapped_column(String(16), nullable=False)
    pet_name: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    risk_text: Mapped[str] = mapped_column(String(16), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    observation_advice: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    diet_advice: Mapped[str] = mapped_column(Text, default="", nullable=False)
    need_vet: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_ai_result: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    user: Mapped[Optional["User"]] = relationship(back_populates="analyses")
    records: Mapped[list["HealthRecord"]] = relationship(back_populates="analysis")
