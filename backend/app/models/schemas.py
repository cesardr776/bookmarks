from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class ScenarioType(str, Enum):
    white_background = "white_background"
    professional_studio = "professional_studio"
    modern_store = "modern_store"
    urban_lifestyle = "urban_lifestyle"


# Prompts calibrated for fashion e-commerce img2img generation
SCENARIO_PROMPTS: dict[ScenarioType, str] = {
    ScenarioType.white_background: (
        "fashion product photo on pure white seamless background, "
        "professional studio lighting, e-commerce quality, high resolution, "
        "clean and minimal, commercial photography"
    ),
    ScenarioType.professional_studio: (
        "high-end fashion studio photography, dramatic softbox lighting, "
        "seamless gray backdrop, editorial quality, sharp details, "
        "professional commercial shoot"
    ),
    ScenarioType.modern_store: (
        "stylish boutique retail interior, modern store display, "
        "warm ambient lighting, premium fashion store setting, "
        "professional product photography"
    ),
    ScenarioType.urban_lifestyle: (
        "urban street style fashion photography, city architecture background, "
        "natural golden hour lighting, editorial lifestyle photo, "
        "authentic outdoor setting"
    ),
}

SCENARIO_NEGATIVE_PROMPTS: dict[ScenarioType, str] = {
    ScenarioType.white_background: "shadows, colored background, props, clutter",
    ScenarioType.professional_studio: "overexposed, flat lighting, amateur",
    ScenarioType.modern_store: "messy, outdated decor, bad lighting",
    ScenarioType.urban_lifestyle: "indoors, studio, plain background",
}


class GenerateResponse(BaseModel):
    image_url: str = Field(..., description="Public URL or local path to generated image")
    filename: str = Field(..., description="Saved filename")
    scenario: ScenarioType
    prompt_used: str = Field(..., description="Full prompt sent to the model")
    model_id: str


class HealthResponse(BaseModel):
    status: str
    version: str
    model_id: str
    storage_dir: str
    stored_images: int
