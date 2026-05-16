import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError, ErrorCode
from app.models.health_record import HealthRecord
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.record_repository import RecordRepository
from app.schemas.record import (
    HealthRecordResponse,
    PaginationResponse,
    RecordListResponse,
    SaveRecordResult,
)
from app.services.analysis_cache_service import AnalysisCacheService


class RecordService:
    def __init__(self, db: Session, redis_client) -> None:
        """Create a record service using database repositories and guest cache."""
        self.db = db
        self.redis = redis_client
        self.record_repository = RecordRepository(db)
        self.analysis_repository = AnalysisRepository(db)
        self.analysis_cache = AnalysisCacheService(redis_client)

    def get_recent_record(self, user_id: str = None, guest_id: str = None) -> HealthRecordResponse:
        """Return the latest saved or guest analysis record for the current identity."""
        if user_id:
            record = self.record_repository.get_recent_for_user(user_id)
            return self._to_response(record) if record else None

        if guest_id:
            analysis_id = self.analysis_cache.get_guest_recent_analysis_id(guest_id)
            if not analysis_id:
                return None
            analysis = self.analysis_repository.get_by_id(analysis_id)
            return self._analysis_to_record_response(analysis) if analysis else None

        return None

    def list_records(self, user_id: str, page: int, page_size: int) -> RecordListResponse:
        """Return a paginated list of saved records for a logged-in user."""
        records, total = self.record_repository.list_for_user(
            user_id=user_id,
            page=max(page, 1),
            page_size=max(min(page_size, 100), 1),
        )
        return RecordListResponse(
            list=[self._to_response(record) for record in records],
            pagination=PaginationResponse(
                page=page,
                page_size=page_size,
                total=total,
                has_more=page * page_size < total,
            ),
        )

    def save_record(self, user_id: str, analysis_id: str) -> SaveRecordResult:
        """Save an accessible analysis as a user's health record."""
        analysis = self.analysis_repository.get_by_id(analysis_id)
        if analysis is None or (analysis.user_id and analysis.user_id != user_id):
            raise BusinessError(ErrorCode.record_not_found, status_code=404)

        existing = self.record_repository.get_by_user_and_analysis(user_id, analysis_id)
        if existing is not None:
            return SaveRecordResult(id=existing.id)

        record = HealthRecord(
            id=self._new_record_id(),
            user_id=user_id,
            analysis_id=analysis_id,
        )
        self.record_repository.create(record)
        self.db.commit()
        return SaveRecordResult(id=record.id)

    def delete_record(self, user_id: str, record_id: str) -> None:
        """Soft-delete a record after verifying user ownership."""
        record = self.record_repository.get_by_id(record_id)
        if record is None or record.user_id != user_id:
            raise BusinessError(ErrorCode.record_not_found, status_code=404)
        self.record_repository.soft_delete(record)
        self.db.commit()

    @staticmethod
    def _to_response(record: HealthRecord) -> HealthRecordResponse:
        """Convert a persisted health record into the frontend record shape."""
        return HealthRecordResponse(
            id=record.id,
            analysis_id=record.analysis_id,
            image_url=record.analysis.image_url,
            score=record.analysis.score,
            risk_level=record.analysis.risk_level,
            risk_text=record.analysis.risk_text,
            summary=record.analysis.summary,
            created_at=record.created_at,
        )

    @staticmethod
    def _analysis_to_record_response(analysis) -> HealthRecordResponse:
        """Represent a guest's recent analysis using the record response shape."""
        return HealthRecordResponse(
            id=analysis.id,
            analysis_id=analysis.id,
            image_url=analysis.image_url,
            score=analysis.score,
            risk_level=analysis.risk_level,
            risk_text=analysis.risk_text,
            summary=analysis.summary,
            created_at=analysis.created_at,
        )

    @staticmethod
    def _new_record_id() -> str:
        """Generate an opaque health record identifier."""
        return f"record_{uuid.uuid4().hex}"
