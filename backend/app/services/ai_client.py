"""
AI client for mrfakename/Z-Image-Turbo img2img generation.

Provider selection (AI_PROVIDER env var, or auto-detected):

  huggingface  →  Hugging Face Inference API  [requires HF_TOKEN]
                  POST https://api-inference.huggingface.co/models/mrfakename/Z-Image-Turbo
                  Real img2img — the input photo IS used.

  local        →  diffusers loaded in-process  [requires GPU + requirements-gpu.txt]
                  AutoPipelineForImage2Image.from_pretrained("mrfakename/Z-Image-Turbo")
                  Real img2img — the input photo IS used.

  runpod       →  RunPod serverless worker     [requires RUNPOD_* vars]
                  POST https://api.runpod.ai/v2/{endpoint}/runsync

  together     →  Together AI text-to-image    [requires TOGETHER_API_KEY]
                  POST https://api.together.xyz/v1/images/generations
                  ⚠ text-to-image only — input photo is NOT used by the model.

Provider priority (auto-detect):  runpod > huggingface > together
"""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import httpx

from app.config import Settings
from app.models.schemas import ScenarioType, SCENARIO_PROMPTS, SCENARIO_NEGATIVE_PROMPTS
from app.services import local_pipeline
from app.utils.image_utils import preprocess, to_base64, from_base64

logger = logging.getLogger(__name__)

# One worker: a single GPU handles one inference at a time
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="diffusers")


class AIClientError(Exception):
    """Raised when the upstream AI service returns an error."""


# ── Shared prompt helpers ─────────────────────────────────────────────────────

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


# ── Option A: Hugging Face Inference API ─────────────────────────────────────

async def _call_huggingface(
    image_bytes: bytes,
    prompt: str,
    negative: str,
    settings: Settings,
) -> bytes:
    """
    Calls the HF Inference API for mrfakename/Z-Image-Turbo.

    The API accepts:
      - Body: raw image bytes (Content-Type: image/jpeg)
      - Headers: prompt and generation parameters passed as X-* headers

    Response: raw JPEG bytes (Content-Type: image/jpeg).

    For models that require warm-up (503 with "loading"), the header
    X-Wait-For-Model: true tells HF to queue the request instead of failing.
    """
    headers = {
        "Authorization": f"Bearer {settings.hf_token}",
        "Content-Type": "image/jpeg",
        "X-Wait-For-Model": "true",
        "X-Use-Cache": "0",
    }
    # HF Inference API passes extra generation params as query parameters
    params = {
        "prompt": prompt,
        "negative_prompt": negative,
        "num_inference_steps": settings.generation_steps,
        "strength": settings.model_strength,
        "guidance_scale": settings.guidance_scale,
        "width": settings.image_width,
        "height": settings.image_height,
    }

    logger.info("Calling HF Inference API model=%s", settings.hf_model_id)

    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        resp = await client.post(
            settings.hf_inference_url,
            content=image_bytes,
            headers=headers,
            params=params,
        )

    if resp.status_code == 503:
        body = resp.text[:300]
        raise AIClientError(
            f"HF model is loading (503). Retry in ~20 s. Detail: {body}"
        )

    if resp.status_code != 200:
        body = resp.text[:500]
        raise AIClientError(
            f"HF Inference API returned {resp.status_code}: {body}"
        )

    content_type = resp.headers.get("content-type", "")
    if "application/json" in content_type:
        # Some HF pipelines return base64 JSON
        data = resp.json()
        if isinstance(data, list) and data:
            # [{"generated_image": "<b64>"}] or similar
            item = data[0]
            b64 = item.get("generated_image") or item.get("image") or ""
            if b64:
                return from_base64(b64)
        raise AIClientError(f"Unexpected JSON shape from HF API: {data}")

    # Standard case: binary JPEG response
    return resp.content


# ── Option B: local diffusers ─────────────────────────────────────────────────

async def _call_local(
    image_bytes: bytes,
    prompt: str,
    negative: str,
    settings: Settings,
) -> bytes:
    """
    Runs inference in a thread executor to avoid blocking the event loop.
    Requires local_pipeline.load() to have been called at startup.
    """
    if not local_pipeline.is_available():
        raise AIClientError(
            "Local inference requires torch + diffusers. "
            "Install: pip install -r requirements-gpu.txt"
        )

    logger.info("Running local diffusers inference model=%s", settings.local_model_id)

    loop = asyncio.get_event_loop()
    result_bytes = await loop.run_in_executor(
        _executor,
        local_pipeline.run,
        image_bytes,
        prompt,
        negative,
        settings.generation_steps,
        settings.model_strength,
        settings.guidance_scale,
        settings.image_width,
        settings.image_height,
    )
    return result_bytes


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
            "strength": settings.model_strength,
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
        raise AIClientError(f"RunPod returned {resp.status_code}: {resp.text[:500]}")

    data = resp.json()
    output = data.get("output", {})
    b64 = (
        output.get("image")
        or (output.get("images") or [""])[0]
        or output.get("b64_json", "")
    )
    if not b64:
        raise AIClientError(f"Could not extract image from RunPod response: {data}")
    return b64


# ── Together AI (text-to-image, legacy) ───────────────────────────────────────

async def _call_together(
    b64_image: str,
    prompt: str,
    negative: str,
    settings: Settings,
) -> str:
    """
    Together AI text-to-image.
    ⚠ The b64_image parameter is sent but Together AI's /images/generations
      endpoint does NOT perform img2img — the input photo is ignored.
      Use huggingface or local for real img2img with Z-Image-Turbo.
    """
    payload = {
        "model": settings.model_id,
        "prompt": prompt,
        "negative_prompt": negative,
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
        resp = await client.post(settings.together_api_url, json=payload, headers=headers)

    if resp.status_code != 200:
        raise AIClientError(f"Together AI returned {resp.status_code}: {resp.text[:500]}")

    data = resp.json()
    try:
        return data["data"][0]["b64_json"]
    except (KeyError, IndexError) as exc:
        raise AIClientError(f"Unexpected Together AI response shape: {exc}") from exc


# ── Public interface ──────────────────────────────────────────────────────────

async def generate(
    image_bytes: bytes,
    scenario: ScenarioType,
    settings: Settings,
    custom_prompt: Optional[str] = None,
) -> tuple[bytes, str]:
    """
    Run img2img generation with the configured provider.

    Returns:
        (jpeg_bytes, prompt_used)
    """
    provider = settings.active_provider

    if provider == "none":
        raise AIClientError(
            "No AI provider configured. "
            "Set HF_TOKEN (huggingface), AI_PROVIDER=local, "
            "RUNPOD_* vars, or TOGETHER_API_KEY."
        )

    processed = preprocess(image_bytes)
    prompt = _build_prompt(scenario, custom_prompt)
    negative = _build_negative(scenario, settings)

    if provider == "huggingface":
        result_bytes = await _call_huggingface(processed, prompt, negative, settings)
        return result_bytes, prompt

    if provider == "local":
        result_bytes = await _call_local(processed, prompt, negative, settings)
        return result_bytes, prompt

    # RunPod and Together AI use base64 for the wire format
    b64_input = to_base64(processed)

    if provider == "runpod":
        b64_result = await _call_runpod(b64_input, prompt, negative, settings)
        return from_base64(b64_result), prompt

    if provider == "together":
        b64_result = await _call_together(b64_input, prompt, negative, settings)
        return from_base64(b64_result), prompt

    raise AIClientError(f"Unknown provider '{provider}'.")
