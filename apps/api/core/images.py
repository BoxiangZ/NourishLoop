from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_UPLOAD_REQUEST_BYTES = MAX_UPLOAD_BYTES + 64 * 1024
MAX_IMAGE_PIXELS = 40_000_000
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


class InvalidImageError(ValueError):
    pass


class ImageTooLargeError(InvalidImageError):
    pass


def detect_image_type(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate_image(data: bytes, declared_type: str) -> str:
    if len(data) > MAX_UPLOAD_BYTES:
        raise ImageTooLargeError("图片不能超过 8 MB")
    if declared_type not in ALLOWED_IMAGE_TYPES:
        raise InvalidImageError("请选择 JPEG、PNG 或 WebP 图片")

    detected_type = detect_image_type(data)
    if detected_type is None:
        raise InvalidImageError("请选择 JPEG、PNG 或 WebP 图片")
    if declared_type != detected_type:
        raise InvalidImageError("图片内容与文件类型不一致")

    try:
        with Image.open(BytesIO(data)) as image:
            image.verify()
        with Image.open(BytesIO(data)) as image:
            width, height = image.size
            if width * height > MAX_IMAGE_PIXELS:
                raise ImageTooLargeError("图片像素尺寸过大")
            image.load()
    except Image.DecompressionBombError as exc:
        raise ImageTooLargeError("图片像素尺寸过大") from exc
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise InvalidImageError("无法读取图片内容") from exc
    return detected_type


def safe_filename(name: str | None) -> str:
    cleaned = Path(name or "").name
    cleaned = re.sub(r"[\x00-\x1f\x7f]", "", cleaned).strip()
    return cleaned[:200] or "meal-image"
