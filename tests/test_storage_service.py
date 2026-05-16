from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.exceptions import BusinessError, ErrorCode
from app.services.storage_service import StorageService


def test_storage_service_saves_and_reads_local_image(tmp_path: Path):
    settings = Settings(
        upload_local_dir=str(tmp_path),
        public_image_base_url="http://localhost/static/uploads",
    )
    service = StorageService(settings=settings)

    image_url = service.save_image("image_001", "png", b"image-bytes")
    content, image_type = service.read_image(image_url)

    assert image_url == "http://localhost/static/uploads/image_001.png"
    assert content == b"image-bytes"
    assert image_type == "png"


def test_storage_service_rejects_unknown_image_url(tmp_path: Path):
    settings = Settings(
        upload_local_dir=str(tmp_path),
        public_image_base_url="http://localhost/static/uploads",
    )
    service = StorageService(settings=settings)

    with pytest.raises(BusinessError) as exc_info:
        service.read_image("https://example.com/image_001.png")

    assert exc_info.value.code == ErrorCode.image_required
