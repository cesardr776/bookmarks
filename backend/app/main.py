from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.models.schemas import HealthResponse
from app.routers import generate
from app.services.storage import count_stored

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    logger.info(
        "Moda IA started | model=%s | provider=%s | storage=%s",
        settings.model_id,
        "RunPod" if settings.use_runpod else "Together AI",
        settings.storage_dir,
    )
    yield
    logger.info("Moda IA shutting down")


settings = get_settings()

app = FastAPI(
    title="Moda IA — Backend",
    description=(
        "Transform clothing photos into professional e-commerce images "
        "using Z-Image-Turbo generative AI."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router, prefix="/api/v1")

# Serve saved images as static files (fallback path)
settings.storage_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    "/storage",
    StaticFiles(directory=str(settings.storage_dir)),
    name="storage",
)


@app.get("/health", response_model=HealthResponse, tags=["ops"])
async def health():
    s = get_settings()
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        model_id=s.model_id,
        storage_dir=str(s.storage_dir),
        stored_images=count_stored(s),
    )


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s", request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )
