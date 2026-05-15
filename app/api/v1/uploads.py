from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import BusinessError, ErrorCode
from app.core.responses import success_response
from app.services.upload_service import UploadService

router = APIRouter(prefix="/uploads")


@router.post("/images")
async def upload_image(
    file: UploadFile = File(...),
    pet_type: str = Form(default=None, alias="petType"),
    db: Session = Depends(get_db),
):
    try:
        content = await file.read()
        result = UploadService(db=db, settings=get_settings()).upload_image(
            content=content,
            pet_type=pet_type,
        )
    except BusinessError:
        raise
    except OSError:
        raise BusinessError(ErrorCode.upload_failed) from None

    return success_response(data=result.model_dump(by_alias=True))
