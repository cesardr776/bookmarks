from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

# Valid provider names
Provider = Literal["local", "huggingface", "runpod", "together"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        protected_namespaces=(),
    )

    # ── Provider selection ────────────────────────────────────────────────────
    # Explicit override. Leave blank to auto-detect from available credentials.
    # Priority (auto):  runpod > huggingface > together
    ai_provider: str = ""

    # ── Hugging Face (Option A — cloud, no local GPU required) ───────────────
    hf_token: str = ""
    hf_model_id: str = "mrfakename/Z-Image-Turbo"

    # ── Local diffusers (Option B — RunPod / own GPU) ────────────────────────
    # ai_provider=local uses these settings
    local_model_id: str = "mrfakename/Z-Image-Turbo"
    device: str = "cuda"             # cuda | cpu | mps
    torch_dtype: str = "float16"     # float16 | bfloat16 | float32

    # ── Legacy providers ──────────────────────────────────────────────────────
    together_api_key: str = ""
    runpod_api_key: str = ""
    runpod_endpoint_id: str = ""
    # model_id used only for Together AI and RunPod
    model_id: str = "black-forest-labs/FLUX.1-schnell"

    # ── Generation parameters (shared across providers) ───────────────────────
    image_width: int = 1024
    image_height: int = 1024
    generation_steps: int = 4        # Turbo/Schnell models converge in 2–4 steps
    guidance_scale: float = 0.0      # SDXL Turbo: 0.0;  SD 1.5: 7.5
    model_strength: float = 0.6      # img2img strength — 0=no change, 1=ignore input
    negative_prompt: str = (
        "blurry, low quality, distorted, watermark, text overlay, "
        "logo, bad anatomy, duplicate, ugly"
    )

    # ── Storage ───────────────────────────────────────────────────────────────
    storage_dir: Path = Path("storage")
    max_stored_images: int = 1000

    # ── Server ────────────────────────────────────────────────────────────────
    cors_origins: str = "*"
    port: int = 8000
    debug: bool = False

    # ── Limits ────────────────────────────────────────────────────────────────
    max_upload_size_mb: int = 10
    request_timeout_seconds: int = 180

    # ── Computed ──────────────────────────────────────────────────────────────

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def active_provider(self) -> str:
        """Resolve the effective provider, explicit setting taking priority."""
        if self.ai_provider:
            return self.ai_provider
        # Auto-detect from available credentials
        if self.runpod_api_key and self.runpod_endpoint_id:
            return "runpod"
        if self.hf_token:
            return "huggingface"
        if self.together_api_key:
            return "together"
        return "none"

    # Kept for backward compatibility with existing tests
    @property
    def use_runpod(self) -> bool:
        return self.active_provider == "runpod"

    @property
    def together_api_url(self) -> str:
        return "https://api.together.xyz/v1/images/generations"

    @property
    def runpod_api_url(self) -> str:
        return f"https://api.runpod.ai/v2/{self.runpod_endpoint_id}/runsync"

    @property
    def hf_inference_url(self) -> str:
        return f"https://api-inference.huggingface.co/models/{self.hf_model_id}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
