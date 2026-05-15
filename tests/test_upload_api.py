from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1 import uploads as uploads_module
from app.core.config import Settings
from app.core.database import get_db
from app.main import app
from app.models import Base
from tests.image_fixtures import PNG_1X1


def build_session_factory():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def test_upload_image_api_success(monkeypatch, tmp_path: Path):
    session_factory = build_session_factory()

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(
        uploads_module,
        "get_settings",
        lambda: Settings(
            upload_local_dir=str(tmp_path),
            public_image_base_url="http://localhost/static/uploads",
        ),
    )
    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    response = client.post(
        "/api/v1/uploads/images",
        data={"petType": "dog"},
        files={"file": ("poop.png", PNG_1X1, "image/png")},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["imageUrl"].startswith("http://localhost/static/uploads/image_")
    assert payload["data"]["imageSha256"]
    assert payload["data"]["width"] == 1
    assert payload["data"]["height"] == 1
    assert payload["data"]["size"] == len(PNG_1X1)


def test_upload_image_api_rejects_invalid_type():
    client = TestClient(app)

    response = client.post(
        "/api/v1/uploads/images",
        files={"file": ("bad.txt", b"bad", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "IMAGE_TYPE_INVALID"

