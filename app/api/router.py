from fastapi import APIRouter

from app.api.v1.analyses import router as analyses_router
from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.records import router as records_router
from app.api.v1.uploads import router as uploads_router

api_router = APIRouter()
api_router.include_router(analyses_router, tags=["analyses"])
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(health_router, tags=["health"])
api_router.include_router(records_router, tags=["records"])
api_router.include_router(uploads_router, tags=["uploads"])
