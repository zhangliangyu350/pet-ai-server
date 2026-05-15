import pytest

from app.core.exceptions import BusinessError, ErrorCode
from app.utils.hashing import sha256_bytes
from app.utils.image import MAX_IMAGE_SIZE, validate_image
from tests.image_fixtures import JPEG_1X1, PNG_1X1


def test_validate_png_reads_dimensions():
    image_info = validate_image(PNG_1X1)

    assert image_info.image_type == "png"
    assert image_info.width == 1
    assert image_info.height == 1
    assert image_info.size == len(PNG_1X1)


def test_validate_jpeg_reads_dimensions():
    image_info = validate_image(JPEG_1X1)

    assert image_info.image_type == "jpg"
    assert image_info.width == 1
    assert image_info.height == 1


def test_validate_image_rejects_invalid_type():
    with pytest.raises(BusinessError) as exc_info:
        validate_image(b"not an image")

    assert exc_info.value.code == ErrorCode.image_type_invalid


def test_validate_image_rejects_large_file():
    with pytest.raises(BusinessError) as exc_info:
        validate_image(b"x" * (MAX_IMAGE_SIZE + 1))

    assert exc_info.value.code == ErrorCode.image_size_exceeded


def test_sha256_bytes_is_stable():
    assert sha256_bytes(b"abc") == sha256_bytes(b"abc")

