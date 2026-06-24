"""
Local diffusers pipeline for mrfakename/Z-Image-Turbo.

This module is only active when AI_PROVIDER=local.  It loads the model once
at FastAPI startup and holds it in memory for the lifetime of the process.

Requirements (install via requirements-gpu.txt):
    torch >= 2.2
    diffusers >= 0.27
    accelerate >= 0.28
    transformers >= 4.38
    safetensors >= 0.4

Usage on RunPod GPU pod:
    pip install -r requirements-gpu.txt
    AI_PROVIDER=local uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Guard: torch/diffusers are optional — only needed for AI_PROVIDER=local
try:
    import torch
    from diffusers import AutoPipelineForImage2Image
    from PIL import Image
    _DIFFUSERS_AVAILABLE = True
except ImportError:
    _DIFFUSERS_AVAILABLE = False

_pipeline = None   # Loaded once on startup


def is_available() -> bool:
    return _DIFFUSERS_AVAILABLE


def load(model_id: str, device: str, dtype_str: str) -> None:
    """
    Load the img2img pipeline.  Call once from the FastAPI lifespan handler.

    Args:
        model_id:  HF model ID, e.g. "mrfakename/Z-Image-Turbo"
        device:    "cuda", "mps", or "cpu"
        dtype_str: "float16", "bfloat16", or "float32"
    """
    global _pipeline

    if not _DIFFUSERS_AVAILABLE:
        raise RuntimeError(
            "torch/diffusers not installed. "
            "Run: pip install -r requirements-gpu.txt"
        )

    dtype_map = {
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "float32": torch.float32,
    }
    dtype = dtype_map.get(dtype_str, torch.float16)

    logger.info("Loading local pipeline model_id=%s device=%s dtype=%s",
                model_id, device, dtype_str)

    pipe = AutoPipelineForImage2Image.from_pretrained(
        model_id,
        torch_dtype=dtype,
        use_safetensors=True,
        variant="fp16" if dtype_str == "float16" else None,
    )

    if device == "cuda":
        # Memory-efficient attention saves ~30% VRAM
        try:
            pipe.enable_xformers_memory_efficient_attention()
            logger.info("xformers memory-efficient attention enabled")
        except Exception:
            logger.info("xformers not available — using default attention")

        # CPU offload allows larger models on 16 GB VRAM pods
        pipe.enable_model_cpu_offload()
    else:
        pipe = pipe.to(device)

    _pipeline = pipe
    logger.info("Pipeline loaded and ready on %s", device)


def run(
    image_bytes: bytes,
    prompt: str,
    negative_prompt: str,
    num_steps: int,
    strength: float,
    guidance_scale: float,
    width: int,
    height: int,
) -> bytes:
    """
    Synchronous inference.  Must be called inside run_in_executor to avoid
    blocking the FastAPI event loop.

    Returns raw JPEG bytes of the generated image.
    """
    if _pipeline is None:
        raise RuntimeError("Pipeline not loaded. Call local_pipeline.load() first.")

    init_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    init_image = init_image.resize((width, height), Image.LANCZOS)

    result = _pipeline(
        prompt=prompt,
        negative_prompt=negative_prompt or None,
        image=init_image,
        num_inference_steps=num_steps,
        strength=strength,
        guidance_scale=guidance_scale,
    ).images[0]

    buf = io.BytesIO()
    result.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def unload() -> None:
    """Release GPU memory on shutdown."""
    global _pipeline
    if _pipeline is not None:
        del _pipeline
        _pipeline = None
        if _DIFFUSERS_AVAILABLE:
            try:
                torch.cuda.empty_cache()
            except Exception:
                pass
        logger.info("Local pipeline unloaded")
