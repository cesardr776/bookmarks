import io
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.models.schemas import GenerateResponse, ScenarioType
from app.services.firebase_service import upload_base64_image
from app.services.image_service import generate_image

router = APIRouter(tags=["generation"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post(
    "/generate",
    response_model=GenerateResponse,
    summary="Generate professional e-commerce image from clothing photo",
)
async def generate_product_image(
    image: UploadFile = File(..., description="Clothing photo (JPEG/PNG/WebP, max 10 MB)"),
    scenario: ScenarioType = Form(
        ScenarioType.WHITE_BACKGROUND,
        description="Background scenario",
    ),
    prompt: Optional[str] = Form(None, description="Optional custom prompt suffix"),
    user_id: Optional[str] = Form(None, description="Firebase user UID"),
):
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{image.content_type}'. Use JPEG, PNG, or WebP.",
        )

    image_bytes = await image.read()

    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image exceeds 10 MB limit.",
        )

    try:
        b64_result = await generate_image(image_bytes, scenario, prompt)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Image generation failed: {str(exc)}",
        )

    try:
        image_url = upload_base64_image(b64_result, user_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage upload failed: {str(exc)}",
        )

    from app.models.schemas import SCENARIO_PROMPTS

    return GenerateResponse(
        image_url=image_url,
        scenario=scenario.value,
        original_prompt=SCENARIO_PROMPTS[scenario],
    )
