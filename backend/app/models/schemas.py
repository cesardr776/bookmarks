from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ScenarioType(str, Enum):
    WHITE_BACKGROUND = "white_background"
    PROFESSIONAL_STUDIO = "professional_studio"
    MODERN_STORE = "modern_store"
    URBAN_LIFESTYLE = "urban_lifestyle"


SCENARIO_PROMPTS = {
    ScenarioType.WHITE_BACKGROUND: (
        "professional e-commerce product photo on clean white background, "
        "perfect studio lighting, high resolution, commercial photography"
    ),
    ScenarioType.PROFESSIONAL_STUDIO: (
        "professional fashion studio photography, dramatic lighting, "
        "seamless backdrop, high-end commercial shoot, editorial quality"
    ),
    ScenarioType.MODERN_STORE: (
        "modern retail store display, stylish boutique interior, "
        "premium fashion store setting, professional commercial photography"
    ),
    ScenarioType.URBAN_LIFESTYLE: (
        "urban lifestyle fashion photography, city street background, "
        "natural light, editorial street style, authentic lifestyle setting"
    ),
}


class GenerateRequest(BaseModel):
    prompt: Optional[str] = Field(None, description="Custom prompt override")
    scenario: ScenarioType = Field(
        ScenarioType.WHITE_BACKGROUND,
        description="Background scenario for the generated image",
    )
    user_id: Optional[str] = Field(None, description="Firebase user UID for storage")


class GenerateResponse(BaseModel):
    image_url: str = Field(..., description="URL of the generated image")
    scenario: str
    original_prompt: str


class HealthResponse(BaseModel):
    status: str
    version: str
