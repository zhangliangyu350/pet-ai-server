from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError, ErrorCode
from app.models.analysis import Analysis
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.image_repository import ImageRepository
from app.schemas.analysis import AnalysisResult, SubmitAnalysisRequest
from app.services.ai_service import DoubaoAIClient
from app.services.analysis_cache_service import AnalysisCacheService
from app.services.analysis_sanitizer import sanitize_ai_result
from app.services.cache_keys import guest_identity, user_identity
from app.services.rate_limit_service import AnalysisRateLimitService
from app.services.storage_service import StorageService


class AnalysisService:
    def __init__(
        self,
        db: Session,
        redis_client,
        ai_client: DoubaoAIClient = None,
        storage_service: StorageService = None,
    ) -> None:
        """创建包含缓存、配额和 AI 依赖的分析流程服务。"""
        self.db = db
        self.redis = redis_client
        self.ai_client = ai_client or DoubaoAIClient()
        self.storage_service = storage_service or StorageService()
        self.analysis_repository = AnalysisRepository(db)
        self.image_repository = ImageRepository(db)
        self.analysis_cache = AnalysisCacheService(redis_client)
        self.rate_limit_service = AnalysisRateLimitService(redis_client)

    async def submit_analysis(
        self,
        payload: SubmitAnalysisRequest,
        user_id: str = None,
        guest_id: str = None,
    ) -> AnalysisResult:
        """执行分析流程：配额检查、缓存查询、AI 调用、持久化和响应转换。"""
        identity, is_guest = self._resolve_identity(user_id=user_id, guest_id=guest_id)
        self.rate_limit_service.check_and_consume(identity=identity, is_guest=is_guest)

        cached_result = self.analysis_cache.get_by_sha256(payload.image_sha256)
        if cached_result is not None:
            if is_guest:
                self.analysis_cache.set_guest_recent_analysis_id(guest_id, cached_result["id"])
            return AnalysisResult.model_validate(cached_result)

        existing_analysis = self.analysis_repository.get_latest_by_sha256(payload.image_sha256)
        if existing_analysis is not None:
            result = self._to_result(existing_analysis)
            self.analysis_cache.set_by_sha256(
                payload.image_sha256,
                result.model_dump(by_alias=True, mode="json"),
            )
            if is_guest:
                self.analysis_cache.set_guest_recent_analysis_id(guest_id, result.id)
            return result

        image_content, image_type = self._read_uploaded_image(
            image_url=payload.image_url,
            image_sha256=payload.image_sha256,
        )
        raw_result = await self.ai_client.analyze_poop_image(
            image_content=image_content,
            image_type=image_type,
            pet_type=payload.pet_type,
            pet_name=payload.pet_name,
        )
        clean_result = sanitize_ai_result(raw_result)
        analysis = Analysis(
            id=self._new_analysis_id(),
            user_id=user_id,
            guest_id=guest_id,
            image_url=payload.image_url,
            image_sha256=payload.image_sha256,
            pet_type=payload.pet_type,
            pet_name=payload.pet_name,
            score=clean_result.score,
            risk_level=clean_result.risk_level,
            risk_text=clean_result.risk_text,
            summary=clean_result.summary,
            observation_advice=clean_result.observation_advice,
            diet_advice=clean_result.diet_advice,
            need_vet=clean_result.need_vet,
            raw_ai_result=raw_result,
        )
        self.analysis_repository.create(analysis)
        self.db.commit()
        result = self._to_result(analysis)
        self.analysis_cache.set_by_sha256(
            payload.image_sha256,
            result.model_dump(by_alias=True, mode="json"),
        )
        if is_guest:
            self.analysis_cache.set_guest_recent_analysis_id(guest_id, result.id)
        return result

    @staticmethod
    def _resolve_identity(user_id: str = None, guest_id: str = None) -> tuple[str, bool]:
        """将当前登录用户或游客解析为限流身份标识。"""
        if user_id:
            return user_identity(user_id), False
        if guest_id:
            return guest_identity(guest_id), True
        raise BusinessError(ErrorCode.auth_required, status_code=401)

    def _read_uploaded_image(self, image_url: str, image_sha256: str) -> tuple[bytes, str]:
        """确认图片来自上传记录，并读取本地图片内容供 AI base64 编码。"""
        image = self.image_repository.get_by_sha256(image_sha256)
        if image is None or image.image_url != image_url:
            raise BusinessError(ErrorCode.image_required)
        return self.storage_service.read_image(image.image_url)

    @staticmethod
    def _to_result(analysis: Analysis) -> AnalysisResult:
        """将分析模型转换为公开分析响应结构。"""
        created_at = analysis.created_at or datetime.utcnow()
        return AnalysisResult(
            id=analysis.id,
            score=analysis.score,
            risk_level=analysis.risk_level,
            risk_text=analysis.risk_text,
            summary=analysis.summary,
            observation_advice=analysis.observation_advice,
            diet_advice=analysis.diet_advice,
            need_vet=analysis.need_vet,
            image_url=analysis.image_url,
            image_sha256=analysis.image_sha256,
            pet_type=analysis.pet_type,
            pet_name=analysis.pet_name,
            created_at=created_at,
        )

    @staticmethod
    def _new_analysis_id() -> str:
        """生成不暴露业务含义的分析 ID。"""
        return f"analysis_{uuid.uuid4().hex}"
