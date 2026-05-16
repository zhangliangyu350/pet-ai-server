from datetime import datetime
from typing import Optional

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.health_record import HealthRecord


class RecordRepository:
    def __init__(self, db: Session) -> None:
        """Create a health record repository bound to a database session."""
        self.db = db

    def get_by_id(self, record_id: str) -> Optional[HealthRecord]:
        """Return a non-deleted health record by primary key."""
        statement = select(HealthRecord).where(
            HealthRecord.id == record_id,
            HealthRecord.deleted_at.is_(None),
        )
        return self.db.execute(statement).scalar_one_or_none()

    def get_by_user_and_analysis(self, user_id: str, analysis_id: str) -> Optional[HealthRecord]:
        """Return an existing saved record for a user and analysis pair."""
        statement = select(HealthRecord).where(
            HealthRecord.user_id == user_id,
            HealthRecord.analysis_id == analysis_id,
            HealthRecord.deleted_at.is_(None),
        )
        return self.db.execute(statement).scalar_one_or_none()

    def get_recent_for_user(self, user_id: str) -> Optional[HealthRecord]:
        """Return the latest non-deleted record saved by a user."""
        statement = (
            select(HealthRecord)
            .where(HealthRecord.user_id == user_id, HealthRecord.deleted_at.is_(None))
            .order_by(desc(HealthRecord.created_at))
            .limit(1)
        )
        return self.db.execute(statement).scalar_one_or_none()

    def list_for_user(
        self,
        user_id: str,
        page: int,
        page_size: int,
    ) -> tuple[list[HealthRecord], int]:
        """Return a page of non-deleted user records and the total count."""
        offset = (page - 1) * page_size
        base_filter = (
            HealthRecord.user_id == user_id,
            HealthRecord.deleted_at.is_(None),
        )
        list_statement = (
            select(HealthRecord)
            .where(*base_filter)
            .order_by(desc(HealthRecord.created_at))
            .offset(offset)
            .limit(page_size)
        )
        count_statement = select(func.count()).select_from(HealthRecord).where(*base_filter)
        records = list(self.db.execute(list_statement).scalars().all())
        total = self.db.execute(count_statement).scalar_one()
        return records, total

    def create(self, record: HealthRecord) -> HealthRecord:
        """Persist a new health record in the current transaction."""
        self.db.add(record)
        self.db.flush()
        return record

    def soft_delete(self, record: HealthRecord) -> HealthRecord:
        """Mark a health record as deleted without removing the row."""
        record.deleted_at = datetime.utcnow()
        self.db.flush()
        return record
