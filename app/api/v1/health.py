from fastapi import APIRouter

from app.core.config import get_settings
from app.core.responses import success_response

router = APIRouter()


@router.get("/health")
def health_check():
    settings = get_settings()
    return success_response(
        data={
            "service": settings.app_name,
            "environment": settings.app_env,
            "status": "ok",
        }
    )

