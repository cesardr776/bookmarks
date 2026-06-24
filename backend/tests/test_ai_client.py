"""Unit tests for the Z-Image-Turbo / Together AI client."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import Settings
from app.models.schemas import ScenarioType
from app.services.ai_client import (
    AIClientError,
    _build_negative,
    _build_prompt,
    generate,
)
from app.utils.image_utils import to_base64
from tests.conftest import make_jpeg_bytes


FAKE_B64 = to_base64(make_jpeg_bytes(64, 64, "green"))
FAKE_JPEG = make_jpeg_bytes(64, 64, "green")


# ── Prompt builders ────────────────────────────────────────────────────────────

class TestBuildPrompt:
    def test_base_only(self):
        p = _build_prompt(ScenarioType.white_background)
        assert "white" in p.lower()

    def test_with_suffix(self):
        p = _build_prompt(ScenarioType.professional_studio, "red silk dress")
        assert p.startswith("red silk dress")

    def test_suffix_stripped(self):
        p = _build_prompt(ScenarioType.urban_lifestyle, "  jeans  ")
        assert p.startswith("jeans")

    def test_empty_suffix_ignored(self):
        p = _build_prompt(ScenarioType.modern_store, "")
        # empty string is falsy — should not prepend
        assert not p.startswith(",")


class TestBuildNegative:
    def test_includes_base_negative(self):
        s = Settings(together_api_key="k")
        neg = _build_negative(ScenarioType.white_background, s)
        assert "blurry" in neg

    def test_scenario_extra_appended(self):
        s = Settings(together_api_key="k")
        neg = _build_negative(ScenarioType.white_background, s)
        # white_background scenario adds "shadows, colored background..."
        assert "shadows" in neg


# ── generate() ────────────────────────────────────────────────────────────────

class TestGenerate:
    @pytest.fixture
    def settings_together(self, tmp_path):
        return Settings(together_api_key="real-key", storage_dir=tmp_path)

    @pytest.fixture
    def settings_runpod(self, tmp_path):
        return Settings(
            runpod_api_key="rp-key",
            runpod_endpoint_id="ep-abc",
            storage_dir=tmp_path,
        )

    @pytest.fixture
    def settings_no_key(self, tmp_path):
        return Settings(together_api_key="", storage_dir=tmp_path)

    # ── no provider configured ─────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_no_provider_raises(self, settings_no_key):
        with pytest.raises(AIClientError, match="No AI provider"):
            await generate(make_jpeg_bytes(), ScenarioType.white_background, settings_no_key)

    # ── Together AI success ────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_together_success(self, settings_together):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": [{"b64_json": FAKE_B64}]
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_resp

            result_bytes, prompt = await generate(
                make_jpeg_bytes(),
                ScenarioType.white_background,
                settings_together,
            )

        assert isinstance(result_bytes, bytes)
        assert len(result_bytes) > 0
        assert "white" in prompt.lower()

    @pytest.mark.asyncio
    async def test_together_http_error_raises(self, settings_together):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_resp

            with pytest.raises(AIClientError, match="401"):
                await generate(
                    make_jpeg_bytes(),
                    ScenarioType.white_background,
                    settings_together,
                )

    @pytest.mark.asyncio
    async def test_together_bad_response_shape_raises(self, settings_together):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"unexpected": "shape"}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_resp

            with pytest.raises(AIClientError):
                await generate(
                    make_jpeg_bytes(),
                    ScenarioType.white_background,
                    settings_together,
                )

    # ── RunPod success ────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_runpod_success(self, settings_runpod):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"output": {"image": FAKE_B64}}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_resp

            result_bytes, _ = await generate(
                make_jpeg_bytes(),
                ScenarioType.urban_lifestyle,
                settings_runpod,
            )

        assert len(result_bytes) > 0

    @pytest.mark.asyncio
    async def test_runpod_empty_output_raises(self, settings_runpod):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"output": {}}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_resp

            with pytest.raises(AIClientError, match="extract image"):
                await generate(
                    make_jpeg_bytes(),
                    ScenarioType.white_background,
                    settings_runpod,
                )

    # ── RunPod takes priority over Together AI ────────────────────────────

    @pytest.mark.asyncio
    async def test_runpod_preferred_when_both_set(self, tmp_path):
        s = Settings(
            together_api_key="together-key",
            runpod_api_key="rp-key",
            runpod_endpoint_id="ep-xyz",
            storage_dir=tmp_path,
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"output": {"image": FAKE_B64}}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_resp

            await generate(make_jpeg_bytes(), ScenarioType.white_background, s)

            # RunPod URL must have been called
            called_url = mock_client.post.call_args[0][0]
            assert "runpod.ai" in called_url

    # ── custom prompt ─────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_custom_prompt_prepended(self, settings_together):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": [{"b64_json": FAKE_B64}]}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_resp

            _, prompt = await generate(
                make_jpeg_bytes(),
                ScenarioType.white_background,
                settings_together,
                custom_prompt="blue denim jacket",
            )

        assert prompt.startswith("blue denim jacket")
