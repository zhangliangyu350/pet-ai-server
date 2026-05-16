import json
import secrets
import uuid

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthSession, LoginResult, UserResponse, WechatSession
from app.services.cache_keys import CacheKeys


class AuthService:
    def __init__(
        self,
        db: Session,
        redis_client,
        session_ttl_seconds: int = 60 * 60 * 24 * 30,
    ) -> None:
        """创建基于数据库和 Redis 会话的认证服务。"""
        self.db = db
        self.redis = redis_client
        self.session_ttl_seconds = session_ttl_seconds
        self.user_repository = UserRepository(db)

    def login_by_wechat(self, wechat_session: WechatSession) -> LoginResult:
        """根据微信身份创建或更新用户，并签发会话 token。"""
        user = self.user_repository.upsert_wechat_user(
            user_id=self._new_user_id(),
            openid=wechat_session.openid,
        )
        token = self._create_session_token(user)
        self.db.commit()
        return LoginResult(token=token, user=self._to_user_response(user))

    def get_session(self, token: str) -> AuthSession:
        """通过 bearer token 加载已认证会话内容。"""
        raw_value = self.redis.get(CacheKeys.session(token))
        if not raw_value:
            return None
        return AuthSession.model_validate(json.loads(raw_value))

    def _create_session_token(self, user: User) -> str:
        """为用户生成并持久化会话 token。"""
        token = secrets.token_urlsafe(32)
        payload = {
            "user_id": user.id,
            "openid": user.openid,
        }
        self.redis.setex(
            CacheKeys.session(token),
            self.session_ttl_seconds,
            json.dumps(payload, ensure_ascii=False),
        )
        return token

    @staticmethod
    def _to_user_response(user: User) -> UserResponse:
        """将用户模型转换为公开登录响应结构。"""
        return UserResponse(
            id=user.id,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            created_at=user.created_at,
        )

    @staticmethod
    def _new_user_id() -> str:
        """生成不暴露业务含义的用户 ID。"""
        return f"user_{uuid.uuid4().hex}"
