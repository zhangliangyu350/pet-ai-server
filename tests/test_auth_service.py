from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.repositories.user_repository import UserRepository
from app.schemas.auth import WechatSession
from app.services.auth_service import AuthService
from app.services.cache_keys import CacheKeys
from tests.fakes import FakeRedis


def build_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    return session_factory()


def test_login_by_wechat_creates_user_and_session():
    db = build_session()
    redis = FakeRedis()
    service = AuthService(db=db, redis_client=redis)

    result = service.login_by_wechat(WechatSession(openid="openid_001"))

    assert result.token
    assert result.user.id.startswith("user_")
    assert result.user.nickname == "微信用户"
    assert redis.get(CacheKeys.session(result.token)) is not None


def test_login_by_wechat_reuses_existing_user():
    db = build_session()
    redis = FakeRedis()
    repository = UserRepository(db)
    user = repository.upsert_wechat_user(user_id="user_001", openid="openid_001")
    db.commit()
    service = AuthService(db=db, redis_client=redis)

    result = service.login_by_wechat(WechatSession(openid="openid_001"))

    assert result.user.id == user.id


def test_auth_service_reads_session():
    db = build_session()
    redis = FakeRedis()
    service = AuthService(db=db, redis_client=redis)
    result = service.login_by_wechat(WechatSession(openid="openid_001"))

    session = service.get_session(result.token)

    assert session.user_id == result.user.id
    assert session.openid == "openid_001"

