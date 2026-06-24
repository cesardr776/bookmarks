"""Unit tests for local filesystem storage."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings
from app.models.schemas import ScenarioType
from app.services.storage import count_stored, get_image_path, save_image
from tests.conftest import make_jpeg_bytes


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(together_api_key="k", storage_dir=tmp_path / "storage")


class TestSaveImage:
    def test_file_created(self, settings):
        filename, path = save_image(make_jpeg_bytes(), ScenarioType.white_background, settings)
        assert path.exists()
        assert path.suffix == ".jpg"

    def test_filename_returned(self, settings):
        filename, _ = save_image(make_jpeg_bytes(), ScenarioType.white_background, settings)
        assert filename.endswith(".jpg")

    def test_stored_under_scenario_dir(self, settings):
        _, path = save_image(make_jpeg_bytes(), ScenarioType.professional_studio, settings)
        assert path.parent.name == "professional_studio"

    def test_content_matches(self, settings):
        data = make_jpeg_bytes(64, 64, "yellow")
        _, path = save_image(data, ScenarioType.white_background, settings)
        assert path.read_bytes() == data

    def test_unique_filenames(self, settings):
        _, p1 = save_image(make_jpeg_bytes(), ScenarioType.white_background, settings)
        _, p2 = save_image(make_jpeg_bytes(), ScenarioType.white_background, settings)
        assert p1 != p2

    def test_rolling_cleanup(self, settings):
        settings.max_stored_images = 3
        for _ in range(5):
            save_image(make_jpeg_bytes(), ScenarioType.white_background, settings)
        remaining = list((settings.storage_dir / "white_background").glob("*.jpg"))
        assert len(remaining) == 3


class TestCountStored:
    def test_empty_storage(self, settings):
        assert count_stored(settings) == 0

    def test_counts_across_scenarios(self, settings):
        save_image(make_jpeg_bytes(), ScenarioType.white_background, settings)
        save_image(make_jpeg_bytes(), ScenarioType.urban_lifestyle, settings)
        save_image(make_jpeg_bytes(), ScenarioType.urban_lifestyle, settings)
        assert count_stored(settings) == 3


class TestGetImagePath:
    def test_returns_correct_path(self, settings):
        filename, saved_path = save_image(
            make_jpeg_bytes(), ScenarioType.modern_store, settings
        )
        retrieved = get_image_path(filename, ScenarioType.modern_store, settings)
        assert retrieved == saved_path

    def test_nonexistent_does_not_raise(self, settings):
        path = get_image_path("ghost.jpg", ScenarioType.white_background, settings)
        assert not path.exists()
