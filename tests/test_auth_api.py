from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1 import auth as auth_module
from app.core.database import get_db
from app.main import app
from app.models import Base
from app.schemas.auth import WechatSession
from tests.fakes import FakeRedis


class MockWechatClient:
    async def code_to_session(self, code: str) -> WechatSession:
        return WechatSession(openid=f"openid_{code}")


def build_session_factory():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def test_wechat_login_api_success(monkeypatch):
    session_factory = build_session_factory()
    redis = FakeRedis()

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(auth_module, "WechatClient", lambda: MockWechatClient())
    monkeypatch.setattr(auth_module, "get_redis_client", lambda: redis)
    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    response = client.post("/api/v1/auth/wechat-login", json={"code": "001"})

    app.dependency_overrides.clear()
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["token"]
    assert payload["data"]["user"]["id"].startswith("user_")
    assert payload["data"]["user"]["nickname"] == "微信用户"
    assert payload["data"]["user"]["avatarUrl"] == ""
    assert payload["message"] == ""


def test_wechat_login_api_validation_error():
    client = TestClient(app)

    response = client.post("/api/v1/auth/wechat-login", json={"code": ""})

    assert response.status_code == 422
    assert response.json() == {
        "success": False,
        "data": None,
        "message": "请检查输入内容",
        "code": "VALIDATION_ERROR",
    }
