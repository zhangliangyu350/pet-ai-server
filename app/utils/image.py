import imghdr
import struct
from dataclasses import dataclass

from app.core.exceptions import BusinessError, ErrorCode

MAX_IMAGE_SIZE = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"jpeg": "jpg", "png": "png"}


@dataclass(frozen=True)
class ImageInfo:
    image_type: str
    width: int
    height: int
    size: int


def validate_image(content: bytes) -> ImageInfo:
    if not content:
        raise BusinessError(ErrorCode.image_required)

    size = len(content)
    if size > MAX_IMAGE_SIZE:
        raise BusinessError(ErrorCode.image_size_exceeded)

    detected_type = imghdr.what(None, content)
    image_type = ALLOWED_IMAGE_TYPES.get(detected_type)
    if image_type is None:
        raise BusinessError(ErrorCode.image_type_invalid)

    width, height = _read_dimensions(content, image_type)
    return ImageInfo(image_type=image_type, width=width, height=height, size=size)


def _read_dimensions(content: bytes, image_type: str) -> tuple[int, int]:
    if image_type == "png":
        return _read_png_dimensions(content)
    return _read_jpeg_dimensions(content)


def _read_png_dimensions(content: bytes) -> tuple[int, int]:
    if len(content) < 24 or not content.startswith(b"\x89PNG\r\n\x1a\n"):
        raise BusinessError(ErrorCode.image_type_invalid)
    width, height = struct.unpack(">II", content[16:24])
    return int(width), int(height)


def _read_jpeg_dimensions(content: bytes) -> tuple[int, int]:
    index = 2
    while index < len(content):
        while index < len(content) and content[index] == 0xFF:
            index += 1
        if index >= len(content):
            break

        marker = content[index]
        index += 1
        if marker in {0xD8, 0xD9}:
            continue
        if index + 2 > len(content):
            break

        segment_length = struct.unpack(">H", content[index : index + 2])[0]
        if segment_length < 2 or index + segment_length > len(content):
            break

        if marker in {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }:
            if index + 7 > len(content):
                break
            height, width = struct.unpack(">HH", content[index + 3 : index + 7])
            return int(width), int(height)

        index += segment_length

    raise BusinessError(ErrorCode.image_type_invalid)

