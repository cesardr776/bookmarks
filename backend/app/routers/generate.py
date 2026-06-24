from __future__ import annotations

import logging
from typing import Annotated, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse

from app.config import Settings, get_settings
from app.models.schemas import GenerateResponse, ScenarioType
from app.services import ai_client, storage
from app.utils.image_utils import ImageError

logger = logging.getLogger(__name__)
router = APIRouter(tags=["generation"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post(
    "/generate",
    response_model=GenerateResponse,
    summary="Generate professional fashion image",
    description=(
        "Upload a clothing photo and choose a background scenario. "
        "The image is processed by Z-Image-Turbo and the result is "
        "saved locally. Returns the download URL and metadata."
    ),
)
async def generate_image(
    request: Request,
    image: Annotated[
        UploadFile,
        File(description="Clothing photo — JPEG, PNG or WebP, max 10 MB"),
    ],
    scenario: Annotated[
        ScenarioType,
        Form(description="Background scenario"),
    ] = ScenarioType.white_background,
    prompt: Annotated[
        Optional[str],
        Form(description="Optional extra description appended to the scenario prompt"),
    ] = None,
    settings: Settings = Depends(get_settings),
):
    # ── Validate content type ───────────────────────────────────────────────
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"'{image.content_type}' is not supported. "
                "Upload a JPEG, PNG, or WebP file."
            ),
        )

    image_bytes = await image.read()

    if len(image_bytes) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.max_upload_size_mb} MB limit.",
        )

    # ── Generate ────────────────────────────────────────────────────────────
    try:
        result_bytes, prompt_used = await ai_client.generate(
            image_bytes=image_bytes,
            scenario=scenario,
            settings=settings,
            custom_prompt=prompt,
        )
    except ai_client.AIClientError as exc:
        logger.error("AI generation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )
    except ImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    # ── Save ────────────────────────────────────────────────────────────────
    filename, _ = storage.save_image(result_bytes, scenario, settings)

    path = request.app.url_path_for("get_image", scenario=scenario.value, filename=filename)
    image_url = str(request.base_url).rstrip("/") + str(path)

    return GenerateResponse(
        image_url=image_url,
        filename=filename,
        scenario=scenario,
        prompt_used=prompt_used,
        model_id=settings.model_id,
    )


@router.get(
    "/images/{scenario}/{filename}",
    summary="Download a generated image",
    name="get_image",
    response_class=FileResponse,
    responses={200: {"content": {"image/jpeg": {}}}},
)
async def get_image(
    scenario: ScenarioType,
    filename: str,
    settings: Settings = Depends(get_settings),
):
    path = storage.get_image_path(filename, scenario, settings)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found.",
        )
    return FileResponse(path, media_type="image/jpeg")
