"""
Local filesystem storage for generated images.

Files are saved under:  storage/<scenario>/<uuid>.jpg
A rolling limit (max_stored_images) prevents unbounded disk use.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from app.config import Settings
from app.models.schemas import ScenarioType

logger = logging.getLogger(__name__)


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _rolling_cleanup(directory: Path, max_files: int) -> None:
    """Delete oldest files in *directory* when count exceeds max_files."""
    files = sorted(directory.glob("*.jpg"), key=lambda f: f.stat().st_mtime)
    excess = max(0, len(files) - max_files)
    for f in files[:excess]:
        try:
            f.unlink()
            logger.debug("Evicted old image: %s", f.name)
        except OSError:
            pass


def save_image(
    image_bytes: bytes,
    scenario: ScenarioType,
    settings: Settings,
) -> tuple[str, Path]:
    """
    Persist image bytes to disk.

    Returns:
        (filename, absolute_path)
    """
    dest_dir = settings.storage_dir / scenario.value
    _ensure_dir(dest_dir)

    filename = f"{uuid.uuid4().hex}.jpg"
    path = dest_dir / filename
    path.write_bytes(image_bytes)
    logger.info("Saved generated image: %s", path)

    _rolling_cleanup(dest_dir, settings.max_stored_images)
    return filename, path.resolve()


def count_stored(settings: Settings) -> int:
    if not settings.storage_dir.exists():
        return 0
    total = 0
    for child in settings.storage_dir.iterdir():
        if child.is_dir():
            total += sum(1 for _ in child.glob("*.jpg"))
    return total


def get_image_path(filename: str, scenario: ScenarioType, settings: Settings) -> Path:
    return settings.storage_dir / scenario.value / filename
