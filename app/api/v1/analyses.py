from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.cache import get_redis_client
from app.core.database import get_db
from app.core.responses import success_response
from app.core.security import get_guest_id, get_optional_user
from app.models.user import User
from app.schemas.analysis import SubmitAnalysisRequest
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/analyses")


@router.post("")
async def submit_analysis(
    payload: SubmitAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user),
    guest_id: str = Depends(get_guest_id),
):
    """提交已上传图片进行 AI 健康分析。"""
    result = await AnalysisService(db=db, redis_client=get_redis_client()).submit_analysis(
        payload=payload,
        user_id=current_user.id if current_user else None,
        guest_id=guest_id,
    )
    return success_response(data=result.model_dump(by_alias=True))
