from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.models import Base
from app.services.upload_service import UploadService
from tests.image_fixtures import PNG_1X1


def build_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    return session_factory()


def test_upload_service_stores_local_image(tmp_path: Path):
    db = build_session()
    settings = Settings(
        upload_local_dir=str(tmp_path),
        public_image_base_url="http://localhost/static/uploads",
    )
    service = UploadService(db=db, settings=settings)

    result = service.upload_image(PNG_1X1, pet_type="cat")

    assert result.image_url.startswith("http://localhost/static/uploads/image_")
    assert result.image_sha256
    assert result.width == 1
    assert result.height == 1
    assert result.size == len(PNG_1X1)
    assert len(list(tmp_path.iterdir())) == 1


def test_upload_service_reuses_existing_sha256(tmp_path: Path):
    db = build_session()
    settings = Settings(
        upload_local_dir=str(tmp_path),
        public_image_base_url="http://localhost/static/uploads",
    )
    service = UploadService(db=db, settings=settings)

    first = service.upload_image(PNG_1X1)
    second = service.upload_image(PNG_1X1)

    assert first.image_sha256 == second.image_sha256
    assert first.image_url == second.image_url
    assert len(list(tmp_path.iterdir())) == 1

