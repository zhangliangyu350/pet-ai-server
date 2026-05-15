from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import get_current_user, get_optional_user
from app.main import app
from app.models.analysis import Analysis
from app.models.user import User
from tests.db_helpers import build_sqlite_session_factory
from tests.fakes import FakeRedis


def seed_data(session_factory):
    db = session_factory()
    user = User(id="user_001", openid="openid_001")
    analysis = Analysis(
        id="analysis_001",
        user_id="user_001",
        image_url="https://example.com/image.jpg",
        image_sha256="sha256_001",
        pet_type="dog",
        pet_name="狗狗",
        score=82,
        risk_level="low",
        risk_text="低风险",
        summary="状态较稳定",
        observation_advice=["继续观察"],
        diet_advice="保持饮水",
        need_vet=False,
        raw_ai_result={},
    )
    db.add_all([user, analysis])
    db.commit()
    db.close()
    return user


def override_db(session_factory):
    def _override():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    return _override


def test_record_api_save_list_recent_and_delete(monkeypatch):
    session_factory = build_sqlite_session_factory()
    user = seed_data(session_factory)
    redis = FakeRedis()

    monkeypatch.setattr("app.api.v1.records.get_redis_client", lambda: redis)
    app.dependency_overrides[get_db] = override_db(session_factory)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_optional_user] = lambda: user

    client = TestClient(app)
    save_response = client.post("/api/v1/records", json={"analysisId": "analysis_001"})
    list_response = client.get("/api/v1/records")
    recent_response = client.get("/api/v1/records/recent")
    record_id = save_response.json()["data"]["id"]
    delete_response = client.delete(f"/api/v1/records/{record_id}")

    app.dependency_overrides.clear()
    assert save_response.status_code == 200
    assert list_response.json()["data"]["pagination"]["total"] == 1
    assert recent_response.json()["data"]["analysisId"] == "analysis_001"
    assert delete_response.json() == {
        "success": True,
        "data": None,
        "message": "删除成功",
    }


def test_records_list_requires_login():
    client = TestClient(app)

    response = client.get("/api/v1/records")

    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_REQUIRED"
