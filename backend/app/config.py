from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        protected_namespaces=(),
    )

    # API keys
    together_api_key: str = ""
    runpod_api_key: str = ""
    runpod_endpoint_id: str = ""

    # Model
    model_id: str = "black-forest-labs/FLUX.1-schnell"
    image_width: int = 1024
    image_height: int = 1024
    generation_steps: int = 4          # FLUX Schnell / Turbo converge fast
    guidance_scale: float = 3.5
    negative_prompt: str = (
        "blurry, low quality, distorted, watermark, text overlay, "
        "logo, bad anatomy, duplicate, ugly"
    )

    # Storage
    storage_dir: Path = Path("storage")
    max_stored_images: int = 1000      # rolling limit, oldest deleted first

    # Server
    cors_origins: str = "*"
    port: int = 8000
    debug: bool = False

    # Limits
    max_upload_size_mb: int = 10
    request_timeout_seconds: int = 180

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def use_runpod(self) -> bool:
        return bool(self.runpod_api_key and self.runpod_endpoint_id)

    @property
    def together_api_url(self) -> str:
        return "https://api.together.xyz/v1/images/generations"

    @property
    def runpod_api_url(self) -> str:
        return f"https://api.runpod.ai/v2/{self.runpod_endpoint_id}/runsync"


@lru_cache
def get_settings() -> Settings:
    return Settings()
