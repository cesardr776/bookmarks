"""Unit tests for image preprocessing utilities."""
from __future__ import annotations

import io

import pytest
from PIL import Image

from app.utils.image_utils import (
    ImageError,
    from_base64,
    image_dimensions,
    preprocess,
    to_base64,
    validate_and_load,
)
from tests.conftest import make_jpeg_bytes, make_png_bytes


class TestValidateAndLoad:
    def test_valid_jpeg(self):
        img = validate_and_load(make_jpeg_bytes())
        assert img.format == "JPEG"

    def test_valid_png(self):
        img = validate_and_load(make_png_bytes())
        assert img.format == "PNG"

    def test_invalid_bytes_raises(self):
        with pytest.raises(ImageError, match="Cannot open image"):
            validate_and_load(b"not an image at all")

    def test_truncated_file_raises(self):
        data = make_jpeg_bytes()[:50]  # truncated
        with pytest.raises(ImageError):
            validate_and_load(data)


class TestPreprocess:
    def test_returns_bytes(self):
        result = preprocess(make_jpeg_bytes())
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_output_is_valid_jpeg(self):
        result = preprocess(make_jpeg_bytes())
        img = Image.open(io.BytesIO(result))
        assert img.format == "JPEG"

    def test_converts_rgba_to_rgb(self):
        result = preprocess(make_png_bytes())
        img = Image.open(io.BytesIO(result))
        assert img.mode == "RGB"

    def test_resizes_large_image(self):
        large = make_jpeg_bytes(2000, 2000)
        result = preprocess(large, max_dim=512)
        w, h = image_dimensions(result)
        assert max(w, h) == 512

    def test_does_not_upscale_small_image(self):
        small = make_jpeg_bytes(100, 80)
        result = preprocess(small, max_dim=1024)
        w, h = image_dimensions(result)
        assert w == 100
        assert h == 80

    def test_preserves_aspect_ratio(self):
        wide = make_jpeg_bytes(1600, 400)
        result = preprocess(wide, max_dim=512)
        w, h = image_dimensions(result)
        assert w == 512
        # height should be proportionally scaled: 400/1600 * 512 = 128
        assert h == 128


class TestBase64Roundtrip:
    def test_encode_decode_roundtrip(self):
        original = make_jpeg_bytes()
        assert from_base64(to_base64(original)) == original

    def test_strips_data_uri_prefix(self):
        raw = make_jpeg_bytes()
        b64 = to_base64(raw)
        uri = f"data:image/jpeg;base64,{b64}"
        assert from_base64(uri) == raw

    def test_empty_bytes(self):
        assert to_base64(b"") == ""
        assert from_base64("") == b""
