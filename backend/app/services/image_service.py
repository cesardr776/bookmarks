import httpx
import base64
import io
import os
import uuid
from typing import Optional

from app.models.schemas import ScenarioType, SCENARIO_PROMPTS
from app.utils.image_utils import resize_image, bytes_to_base64

TOGETHER_API_URL = "https://api.together.xyz/v1/images/generations"
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "")

# RunPod serverless endpoint (overrides Together AI when set)
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID", "")
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", "")
RUNPOD_API_URL = (
    f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/runsync"
    if RUNPOD_ENDPOINT_ID
    else ""
)

MODEL_ID = os.getenv("MODEL_ID", "stabilityai/stable-diffusion-xl-base-1.0")
IMAGE_WIDTH = int(os.getenv("IMAGE_WIDTH", "1024"))
IMAGE_HEIGHT = int(os.getenv("IMAGE_HEIGHT", "1024"))
GENERATION_STEPS = int(os.getenv("GENERATION_STEPS", "30"))
GUIDANCE_SCALE = float(os.getenv("GUIDANCE_SCALE", "7.5"))


def _build_full_prompt(
    scenario: ScenarioType, custom_prompt: Optional[str] = None
) -> str:
    base = SCENARIO_PROMPTS[scenario]
    if custom_prompt:
        return f"{custom_prompt}, {base}"
    return base


async def generate_image_together(
    image_bytes: bytes,
    scenario: ScenarioType,
    custom_prompt: Optional[str] = None,
) -> str:
    resized = resize_image(image_bytes)
    b64_image = bytes_to_base64(resized)
    prompt = _build_full_prompt(scenario, custom_prompt)

    payload = {
        "model": MODEL_ID,
        "prompt": prompt,
        "negative_prompt": (
            "blurry, low quality, distorted, watermark, text, logo, "
            "bad anatomy, ugly, duplicate"
        ),
        "image": f"data:image/jpeg;base64,{b64_image}",
        "width": IMAGE_WIDTH,
        "height": IMAGE_HEIGHT,
        "steps": GENERATION_STEPS,
        "guidance": GUIDANCE_SCALE,
        "n": 1,
        "response_format": "b64_json",
    }

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(TOGETHER_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    b64_result = data["data"][0]["b64_json"]
    return b64_result


async def generate_image_runpod(
    image_bytes: bytes,
    scenario: ScenarioType,
    custom_prompt: Optional[str] = None,
) -> str:
    resized = resize_image(image_bytes)
    b64_image = bytes_to_base64(resized)
    prompt = _build_full_prompt(scenario, custom_prompt)

    payload = {
        "input": {
            "prompt": prompt,
            "negative_prompt": (
                "blurry, low quality, distorted, watermark, text, logo"
            ),
            "image": b64_image,
            "width": IMAGE_WIDTH,
            "height": IMAGE_HEIGHT,
            "num_inference_steps": GENERATION_STEPS,
            "guidance_scale": GUIDANCE_SCALE,
        }
    }

    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(RUNPOD_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    output = data.get("output", {})
    return output.get("image", output.get("images", [""])[0])


async def generate_image(
    image_bytes: bytes,
    scenario: ScenarioType,
    custom_prompt: Optional[str] = None,
) -> str:
    if RUNPOD_ENDPOINT_ID and RUNPOD_API_KEY:
        return await generate_image_runpod(image_bytes, scenario, custom_prompt)
    return await generate_image_together(image_bytes, scenario, custom_prompt)
