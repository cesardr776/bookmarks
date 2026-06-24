"""Integration tests for POST /api/v1/generate and GET /api/v1/images/…"""
from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from tests.conftest import make_jpeg_bytes, make_png_bytes


ENDPOINT = "/api/v1/generate"


def _upload(client: TestClient, image_bytes: bytes, content_type: str = "image/jpeg", **form):
    return client.post(
        ENDPOINT,
        files={"image": ("photo.jpg", io.BytesIO(image_bytes), content_type)},
        data={"scenario": "white_background", **form},
    )


# ── Happy path ─────────────────────────────────────────────────────────────────

class TestGenerateSuccess:
    def test_returns_200_with_image_url(self, client, mock_ai_generate):
        resp = _upload(client, make_jpeg_bytes())
        assert resp.status_code == 200
        body = resp.json()
        assert "image_url" in body
        assert body["image_url"].endswith(".jpg")

    def test_response_contains_all_fields(self, client, mock_ai_generate):
        resp = _upload(client, make_jpeg_bytes())
        body = resp.json()
        assert {"image_url", "filename", "scenario", "prompt_used", "model_id"} <= body.keys()

    def test_image_saved_to_disk(self, client, mock_ai_generate, test_settings):
        _upload(client, make_jpeg_bytes())
        saved = list((test_settings.storage_dir / "white_background").glob("*.jpg"))
        assert len(saved) == 1

    def test_accepts_png(self, client, mock_ai_generate):
        resp = _upload(client, make_png_bytes(), content_type="image/png")
        assert resp.status_code == 200

    def test_custom_prompt_accepted(self, client, mock_ai_generate):
        resp = _upload(client, make_jpeg_bytes(), prompt="red silk dress")
        assert resp.status_code == 200

    def test_all_scenarios_accepted(self, client, mock_ai_generate):
        for scenario in ("white_background", "professional_studio", "modern_store", "urban_lifestyle"):
            resp = client.post(
                ENDPOINT,
                files={"image": ("p.jpg", io.BytesIO(make_jpeg_bytes()), "image/jpeg")},
                data={"scenario": scenario},
            )
            assert resp.status_code == 200, f"Failed for scenario: {scenario}"

    def test_scenario_in_response(self, client, mock_ai_generate):
        resp = _upload(client, make_jpeg_bytes())
        assert resp.json()["scenario"] == "white_background"

    def test_model_id_in_response(self, client, mock_ai_generate):
        resp = _upload(client, make_jpeg_bytes())
        assert resp.json()["model_id"] == "black-forest-labs/FLUX.1-schnell"


# ── Validation errors ──────────────────────────────────────────────────────────

class TestGenerateValidation:
    def test_missing_image_returns_422(self, client):
        resp = client.post(ENDPOINT, data={"scenario": "white_background"})
        assert resp.status_code == 422

    def test_unsupported_content_type_returns_415(self, client, mock_ai_generate):
        resp = _upload(client, b"fake", content_type="image/gif")
        assert resp.status_code == 415

    def test_invalid_scenario_returns_422(self, client, mock_ai_generate):
        resp = client.post(
            ENDPOINT,
            files={"image": ("p.jpg", io.BytesIO(make_jpeg_bytes()), "image/jpeg")},
            data={"scenario": "invalid_scene"},
        )
        assert resp.status_code == 422

    def test_oversized_image_returns_413(self, tmp_path):
        from app.config import get_settings
        from app.main import app

        tiny_limit = Settings(
            together_api_key="k",
            storage_dir=tmp_path,
            max_upload_size_mb=0,
        )
        app.dependency_overrides[get_settings] = lambda: tiny_limit
        get_settings.cache_clear()

        try:
            from fastapi.testclient import TestClient
            c = TestClient(app, raise_server_exceptions=False)
            resp = _upload(c, make_jpeg_bytes(100, 100))
            assert resp.status_code == 413
        finally:
            app.dependency_overrides.clear()
            get_settings.cache_clear()


# ── AI client errors ───────────────────────────────────────────────────────────

class TestGenerateAIErrors:
    def test_ai_error_returns_502(self, client):
        from app.services.ai_client import AIClientError

        with patch(
            "app.services.ai_client.generate",
            new=AsyncMock(side_effect=AIClientError("model timeout")),
        ):
            resp = _upload(client, make_jpeg_bytes())

        assert resp.status_code == 502
        assert "model timeout" in resp.json()["detail"]


# ── Image download endpoint ────────────────────────────────────────────────────

class TestGetImage:
    def test_download_generated_image(self, client, mock_ai_generate, test_settings):
        gen_resp = _upload(client, make_jpeg_bytes())
        assert gen_resp.status_code == 200

        image_url = gen_resp.json()["image_url"]
        # image_url is absolute; extract path after host
        path = "/" + "/".join(image_url.split("/")[3:])

        dl_resp = client.get(path)
        assert dl_resp.status_code == 200
        assert dl_resp.headers["content-type"] == "image/jpeg"

    def test_missing_image_returns_404(self, client):
        resp = client.get("/api/v1/images/white_background/nonexistent.jpg")
        assert resp.status_code == 404


# ── Health endpoint ────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_body(self, client):
        body = client.get("/health").json()
        assert body["status"] == "healthy"
        assert "model_id" in body
        assert "stored_images" in body
