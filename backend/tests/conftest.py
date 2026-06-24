"""Shared fixtures for the test suite."""
from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.config import Settings, get_settings
from app.main import app


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_jpeg_bytes(width: int = 100, height: int = 100, color: str = "red") -> bytes:
    """Create a minimal in-memory JPEG for upload tests."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_png_bytes(width: int = 50, height: int = 50) -> bytes:
    img = Image.new("RGBA", (width, height), color=(0, 128, 255, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ── Settings override ──────────────────────────────────────────────────────────

@pytest.fixture
def tmp_storage(tmp_path: Path) -> Path:
    return tmp_path / "storage"


@pytest.fixture
def test_settings(tmp_storage: Path) -> Settings:
    s = Settings(
        together_api_key="test-key-abc",
        model_id="black-forest-labs/FLUX.1-schnell",
        storage_dir=tmp_storage,
        debug=True,
    )
    return s


@pytest.fixture(autouse=True)
def override_settings(test_settings: Settings):
    """Replace the cached settings singleton for every test."""
    app.dependency_overrides[get_settings] = lambda: test_settings
    get_settings.cache_clear()
    yield
    app.dependency_overrides.clear()
    get_settings.cache_clear()


# ── Client ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


# ── AI mock ────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_ai_generate():
    """
    Patches ai_client.generate to return a valid JPEG without hitting Together AI.
    """
    fake_jpeg = make_jpeg_bytes(256, 256, color="blue")

    with patch(
        "app.services.ai_client.generate",
        new=AsyncMock(return_value=(fake_jpeg, "mocked prompt")),
    ) as mock:
        yield mock
