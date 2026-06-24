from __future__ import annotations

import base64
import io
from pathlib import Path

from PIL import Image, ImageOps

MAX_DIMENSION = 1024
JPEG_QUALITY = 92
SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}


class ImageError(Exception):
    pass


def validate_and_load(data: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(data))
        img.verify()                  # detects truncated files
        img = Image.open(io.BytesIO(data))  # reopen after verify
    except Exception as exc:
        raise ImageError(f"Cannot open image: {exc}") from exc

    if img.format not in SUPPORTED_FORMATS:
        raise ImageError(
            f"Unsupported format '{img.format}'. Use JPEG, PNG, or WebP."
        )
    return img


def preprocess(image_bytes: bytes, max_dim: int = MAX_DIMENSION) -> bytes:
    img = validate_and_load(image_bytes)

    # Normalise orientation from EXIF
    img = ImageOps.exif_transpose(img)

    # Convert to RGB (handles RGBA, P palette, CMYK)
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Resize keeping aspect ratio
    w, h = img.size
    if w > max_dim or h > max_dim:
        ratio = min(max_dim / w, max_dim / h)
        new_w, new_h = int(w * ratio), int(h * ratio)
        img = img.resize((new_w, new_h), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return buf.getvalue()


def to_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


def from_base64(b64: str) -> bytes:
    # Strip data URI prefix if present
    if "," in b64:
        b64 = b64.split(",", 1)[1]
    return base64.b64decode(b64)


def save_to_disk(image_bytes: bytes, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(image_bytes)


def image_dimensions(data: bytes) -> tuple[int, int]:
    img = Image.open(io.BytesIO(data))
    return img.size  # (width, height)
