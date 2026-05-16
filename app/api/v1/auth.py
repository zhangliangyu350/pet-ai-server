from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.cache import get_redis_client
from app.core.database import get_db
from app.core.responses import success_response
from app.schemas.auth import WechatLoginRequest
from app.services.auth_service import AuthService
from app.services.wechat_client import WechatClient

router = APIRouter(prefix="/auth")


@router.post("/wechat-login")
async def wechat_login(payload: WechatLoginRequest, db: Session = Depends(get_db)):
    """使用微信登录 code 换取应用会话 token。"""
    wechat_session = await WechatClient().code_to_session(payload.code)
    auth_service = AuthService(db=db, redis_client=get_redis_client())
    result = auth_service.login_by_wechat(wechat_session)
    return success_response(data=result.model_dump(by_alias=True))
