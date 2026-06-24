import base64
import io
from PIL import Image


MAX_DIMENSION = 1024
JPEG_QUALITY = 90


def resize_image(image_bytes: bytes, max_dim: int = MAX_DIMENSION) -> bytes:
    img = Image.open(io.BytesIO(image_bytes))

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    w, h = img.size
    if w > max_dim or h > max_dim:
        ratio = min(max_dim / w, max_dim / h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

    output = io.BytesIO()
    img.save(output, format="JPEG", quality=JPEG_QUALITY)
    return output.getvalue()


def bytes_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def base64_to_bytes(b64_string: str) -> bytes:
    return base64.b64decode(b64_string)
