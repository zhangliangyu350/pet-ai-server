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
        """创建使用数据库仓储和游客缓存的记录服务。"""
        self.db = db
        self.redis = redis_client
        self.record_repository = RecordRepository(db)
        self.analysis_repository = AnalysisRepository(db)
        self.analysis_cache = AnalysisCacheService(redis_client)

    def get_recent_record(self, user_id: str = None, guest_id: str = None) -> HealthRecordResponse:
        """返回当前身份下最近保存的记录或游客分析记录。"""
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
        """返回登录用户已保存记录的分页列表。"""
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
        """将可访问的分析结果保存为用户健康记录。"""
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
        """校验用户归属后软删除记录。"""
        record = self.record_repository.get_by_id(record_id)
        if record is None or record.user_id != user_id:
            raise BusinessError(ErrorCode.record_not_found, status_code=404)
        self.record_repository.soft_delete(record)
        self.db.commit()

    @staticmethod
    def _to_response(record: HealthRecord) -> HealthRecordResponse:
        """将持久化健康记录转换为前端记录结构。"""
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
        """用记录响应结构表示游客最近一次分析。"""
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
        """生成不暴露业务含义的健康记录 ID。"""
        return f"record_{uuid.uuid4().hex}"
