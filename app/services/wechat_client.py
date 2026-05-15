import logging

import httpx

from app.core.config import get_settings
from app.core.exceptions import BusinessError, ErrorCode
from app.schemas.auth import WechatSession

logger = logging.getLogger(__name__)


class WechatClient:
    code2session_url = "https://api.weixin.qq.com/sns/jscode2session"

    def __init__(
        self,
        app_id: str = None,
        app_secret: str = None,
        timeout_seconds: float = 5.0,
    ) -> None:
        settings = get_settings()
        self.app_id = app_id if app_id is not None else settings.wechat_app_id
        self.app_secret = app_secret if app_secret is not None else settings.wechat_app_secret
        self.timeout_seconds = timeout_seconds

    async def code_to_session(self, code: str) -> WechatSession:
        if not self.app_id or not self.app_secret:
            logger.warning("Wechat login attempted without app credentials configured")
            raise BusinessError(ErrorCode.login_failed)

        params = {
            "appid": self.app_id,
            "secret": self.app_secret,
            "js_code": code,
            "grant_type": "authorization_code",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(self.code2session_url, params=params)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError):
            logger.warning("Wechat code2session request failed")
            raise BusinessError(ErrorCode.login_failed) from None

        if payload.get("errcode"):
            logger.info("Wechat code2session returned errcode=%s", payload.get("errcode"))
            raise BusinessError(ErrorCode.login_failed)

        openid = payload.get("openid")
        if not openid:
            raise BusinessError(ErrorCode.login_failed)

        return WechatSession(
            openid=openid,
            session_key=payload.get("session_key", ""),
            unionid=payload.get("unionid", ""),
        )

