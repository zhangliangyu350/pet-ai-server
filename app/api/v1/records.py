from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.cache import get_redis_client
from app.core.database import get_db
from app.core.responses import success_response
from app.core.security import get_current_user, get_guest_id, get_optional_user
from app.models.user import User
from app.schemas.record import SaveRecordRequest
from app.services.record_service import RecordService

router = APIRouter(prefix="/records")


@router.get("/recent")
def get_recent_record(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user),
    guest_id: str = Depends(get_guest_id),
):
    result = RecordService(db=db, redis_client=get_redis_client()).get_recent_record(
        user_id=current_user.id if current_user else None,
        guest_id=guest_id,
    )
    return success_response(data=result.model_dump(by_alias=True) if result else None)


@router.get("")
def get_records(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = RecordService(db=db, redis_client=get_redis_client()).list_records(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    return success_response(data=result.model_dump(by_alias=True))


@router.post("")
def save_record(
    payload: SaveRecordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = RecordService(db=db, redis_client=get_redis_client()).save_record(
        user_id=current_user.id,
        analysis_id=payload.analysis_id,
    )
    return success_response(data=result.model_dump(), message="保存成功")


@router.delete("/{record_id}")
def delete_record(
    record_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    RecordService(db=db, redis_client=get_redis_client()).delete_record(
        user_id=current_user.id,
        record_id=record_id,
    )
    return success_response(data=None, message="删除成功")

