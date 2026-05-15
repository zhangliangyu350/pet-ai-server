from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.analysis import Analysis
    from app.models.user import User


class HealthRecord(Base):
    __tablename__ = "health_records"
    __table_args__ = (UniqueConstraint("user_id", "analysis_id", name="uq_record_user_analysis"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), index=True, nullable=False)
    analysis_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("analyses.id"),
        index=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="records")
    analysis: Mapped["Analysis"] = relationship(back_populates="records")
