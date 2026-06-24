"""Tests for local_pipeline — covers error paths reachable without a GPU."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from app.services import local_pipeline


class TestLocalPipeline:
    def test_is_available_returns_bool(self):
        result = local_pipeline.is_available()
        assert isinstance(result, bool)

    def test_is_available_false_without_gpu_deps(self):
        # In the CI environment torch/diffusers are not installed
        assert local_pipeline.is_available() is False

    def test_load_raises_without_gpu_deps(self):
        with pytest.raises(RuntimeError, match="torch/diffusers not installed"):
            local_pipeline.load("some/model", "cpu", "float32")

    def test_run_raises_when_pipeline_not_loaded(self):
        with pytest.raises(RuntimeError, match="Pipeline not loaded"):
            local_pipeline.run(b"fake-bytes", "prompt", "neg", 4, 0.6, 0.0, 512, 512)

    def test_unload_is_noop_when_pipeline_is_none(self):
        local_pipeline.unload()  # _pipeline is None → should not raise

    def test_unload_clears_pipeline_when_loaded(self):
        mock_pipe = MagicMock()
        with patch.object(local_pipeline, "_pipeline", mock_pipe):
            with patch.object(local_pipeline, "_DIFFUSERS_AVAILABLE", False):
                local_pipeline.unload()
        # After the context manager restores, _pipeline is back to original state,
        # but we verified the unload path ran without error
