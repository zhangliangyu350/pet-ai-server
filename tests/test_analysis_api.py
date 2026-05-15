from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1 import analyses as analyses_module
from app.core.database import get_db
from app.main import app
from app.schemas.analysis import AnalysisResult, SubmitAnalysisRequest
from tests.db_helpers import build_sqlite_session_factory


class MockAnalysisService:
    def __init__(self, db: Session, redis_client) -> None:
        pass

    async def submit_analysis(
        self,
        payload: SubmitAnalysisRequest,
        user_id: str = None,
        guest_id: str = None,
    ) -> AnalysisResult:
        return AnalysisResult(
            id="analysis_001",
            score=82,
            riskLevel="low",
            riskText="低风险",
            summary="状态较稳定",
            observationAdvice=["继续观察"],
            dietAdvice="保持饮水",
            needVet=False,
            imageUrl=payload.image_url,
            imageSha256=payload.image_sha256,
            petType=payload.pet_type,
            petName=payload.pet_name,
            createdAt="2026-05-16T10:00:00",
        )


def test_submit_analysis_api_supports_guest(monkeypatch):
    session_factory = build_sqlite_session_factory()

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(analyses_module, "AnalysisService", MockAnalysisService)
    monkeypatch.setattr(analyses_module, "get_redis_client", lambda: None)
    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    response = client.post(
        "/api/v1/analyses",
        headers={"X-Guest-Id": "guest_001"},
        json={
            "imageUrl": "https://example.com/image.jpg",
            "imageSha256": "sha256_001",
            "petType": "dog",
            "petName": "狗狗",
        },
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["id"] == "analysis_001"
    assert payload["data"]["riskLevel"] == "low"


def test_submit_analysis_api_validates_pet_type():
    client = TestClient(app)

    response = client.post(
        "/api/v1/analyses",
        headers={"X-Guest-Id": "guest_001"},
        json={
            "imageUrl": "https://example.com/image.jpg",
            "imageSha256": "sha256_001",
            "petType": "bird",
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"

