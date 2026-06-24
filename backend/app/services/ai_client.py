"""
Z-Image-Turbo / Together AI client for img2img fashion photography generation.

Together AI hosts Z-Image-Turbo (and compatible models such as FLUX.1-schnell)
under the unified /v1/images/generations endpoint.  The client also supports
RunPod serverless workers running the same model, selected automatically when
RUNPOD_ENDPOINT_ID and RUNPOD_API_KEY are both set.

API reference:
  https://docs.together.ai/reference/post_images-generations
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import httpx

from app.config import Settings
from app.models.schemas import ScenarioType, SCENARIO_PROMPTS, SCENARIO_NEGATIVE_PROMPTS
from app.utils.image_utils import preprocess, to_base64, from_base64

logger = logging.getLogger(__name__)


class AIClientError(Exception):
    """Raised when the upstream AI service returns an error."""


def _build_prompt(
    scenario: ScenarioType,
    custom_suffix: Optional[str] = None,
) -> str:
    base = SCENARIO_PROMPTS[scenario]
    return f"{custom_suffix.strip()}, {base}" if custom_suffix else base


def _build_negative(scenario: ScenarioType, settings: Settings) -> str:
    extra = SCENARIO_NEGATIVE_PROMPTS.get(scenario, "")
    base = settings.negative_prompt
    return f"{base}, {extra}" if extra else base


# ── Together AI ───────────────────────────────────────────────────────────────

async def _call_together(
    b64_image: str,
    prompt: str,
    negative: str,
    settings: Settings,
) -> str:
    """Returns base64-encoded JPEG of the generated image."""
    payload = {
        "model": settings.model_id,
        "prompt": prompt,
        "negative_prompt": negative,
        "image": f"data:image/jpeg;base64,{b64_image}",
        "width": settings.image_width,
        "height": settings.image_height,
        "steps": settings.generation_steps,
        "guidance": settings.guidance_scale,
        "n": 1,
        "response_format": "b64_json",
    }

    headers = {
        "Authorization": f"Bearer {settings.together_api_key}",
        "Content-Type": "application/json",
    }

    logger.info("Calling Together AI model=%s", settings.model_id)

    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        resp = await client.post(
            settings.together_api_url,
            json=payload,
            headers=headers,
        )

    if resp.status_code != 200:
        body = resp.text[:500]
        raise AIClientError(
            f"Together AI returned {resp.status_code}: {body}"
        )

    data = resp.json()
    try:
        return data["data"][0]["b64_json"]
    except (KeyError, IndexError) as exc:
        raise AIClientError(f"Unexpected Together AI response shape: {exc}") from exc


# ── RunPod serverless ─────────────────────────────────────────────────────────

async def _call_runpod(
    b64_image: str,
    prompt: str,
    negative: str,
    settings: Settings,
) -> str:
    """Returns base64-encoded JPEG from a RunPod serverless worker."""
    payload = {
        "input": {
            "prompt": prompt,
            "negative_prompt": negative,
            "image": b64_image,
            "width": settings.image_width,
            "height": settings.image_height,
            "num_inference_steps": settings.generation_steps,
            "guidance_scale": settings.guidance_scale,
        }
    }

    headers = {
        "Authorization": f"Bearer {settings.runpod_api_key}",
        "Content-Type": "application/json",
    }

    logger.info("Calling RunPod endpoint=%s", settings.runpod_endpoint_id)

    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        resp = await client.post(settings.runpod_api_url, json=payload, headers=headers)

    if resp.status_code != 200:
        body = resp.text[:500]
        raise AIClientError(f"RunPod returned {resp.status_code}: {body}")

    data = resp.json()
    output = data.get("output", {})

    # RunPod handlers vary — try common shapes
    b64 = (
        output.get("image")
        or (output.get("images") or [""])[0]
        or output.get("b64_json", "")
    )
    if not b64:
        raise AIClientError(f"Could not extract image from RunPod response: {data}")
    return b64


# ── Public interface ──────────────────────────────────────────────────────────

async def generate(
    image_bytes: bytes,
    scenario: ScenarioType,
    settings: Settings,
    custom_prompt: Optional[str] = None,
) -> tuple[bytes, str]:
    """
    Run img2img generation.

    Returns:
        (jpeg_bytes, prompt_used)
    """
    if not settings.use_runpod and not settings.together_api_key:
        raise AIClientError(
            "No AI provider configured. Set TOGETHER_API_KEY (or RUNPOD_* vars)."
        )

    processed = preprocess(image_bytes)
    b64_input = to_base64(processed)

    prompt = _build_prompt(scenario, custom_prompt)
    negative = _build_negative(scenario, settings)

    if settings.use_runpod:
        b64_result = await _call_runpod(b64_input, prompt, negative, settings)
    else:
        b64_result = await _call_together(b64_input, prompt, negative, settings)

    result_bytes = from_base64(b64_result)
    return result_bytes, prompt
