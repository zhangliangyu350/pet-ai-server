from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.cache import get_redis_client
from app.core.database import get_db
from app.core.exceptions import BusinessError, ErrorCode
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService


def _extract_bearer_token(authorization: str = None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise BusinessError(ErrorCode.auth_required, status_code=401)
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise BusinessError(ErrorCode.auth_required, status_code=401)
    return token


def get_current_user(
    authorization: str = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> User:
    token = _extract_bearer_token(authorization)
    auth_service = AuthService(db=db, redis_client=get_redis_client())
    session = auth_service.get_session(token)
    if session is None:
        raise BusinessError(ErrorCode.auth_required, status_code=401)

    user = UserRepository(db).get_by_id(session.user_id)
    if user is None:
        raise BusinessError(ErrorCode.auth_required, status_code=401)
    return user


def get_optional_user(
    authorization: str = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> User:
    if not authorization:
        return None
    return get_current_user(authorization=authorization, db=db)


def get_guest_id(x_guest_id: str = Header(default=None, alias="X-Guest-Id")) -> str:
    return x_guest_id
