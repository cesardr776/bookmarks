# Moda IA — Backend

FastAPI backend that transforms clothing photos into professional e-commerce images
using **Z-Image-Turbo** via the Together AI img2img API.

## Architecture

```
app/
├── config.py            # Pydantic-settings (all config from env vars)
├── main.py              # FastAPI app, CORS, lifespan, static mount
├── routers/
│   └── generate.py      # POST /generate  +  GET /images/:scenario/:file
├── services/
│   ├── ai_client.py     # Z-Image-Turbo / Together AI / RunPod HTTP client
│   └── storage.py       # Local filesystem persistence + rolling eviction
├── models/
│   └── schemas.py       # Pydantic schemas + scenario prompts
└── utils/
    └── image_utils.py   # Resize, EXIF fix, base64, format validation
```

## Quick start

### 1. Install

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env — add your TOGETHER_API_KEY (minimum required)
```

### 3. Run

```bash
uvicorn app.main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs   (Swagger UI)
```

## API

### `POST /api/v1/generate`

Upload a clothing photo and get a professional e-commerce image back.

**Request** — `multipart/form-data`

| Field      | Type   | Required | Description |
|------------|--------|----------|-------------|
| `image`    | file   | ✅       | JPEG / PNG / WebP, max 10 MB |
| `scenario` | string | ✅       | See table below |
| `prompt`   | string | ❌       | Extra description appended to scenario prompt |

**Scenarios**

| Value                 | Description |
|-----------------------|-------------|
| `white_background`    | Pure white seamless (default) |
| `professional_studio` | Gray backdrop, softbox |
| `modern_store`        | Boutique interior |
| `urban_lifestyle`     | City street, outdoor |

**Response — 200**

```json
{
  "image_url": "http://localhost:8000/api/v1/images/white_background/abc123.jpg",
  "filename": "abc123.jpg",
  "scenario": "white_background",
  "prompt_used": "professional e-commerce product photo on pure white...",
  "model_id": "black-forest-labs/FLUX.1-schnell"
}
```

**cURL example**

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -F "image=@shirt.jpg" \
  -F "scenario=white_background" \
  -F "prompt=white cotton t-shirt"
```

### `GET /api/v1/images/{scenario}/{filename}`

Download a previously generated image.

```bash
curl -O http://localhost:8000/api/v1/images/white_background/abc123.jpg
```

### `GET /health`

```json
{ "status": "healthy", "version": "1.0.0", "model_id": "...", "stored_images": 7 }
```

## Z-Image-Turbo configuration

Together AI hosts Z-Image-Turbo under their unified `/v1/images/generations` endpoint.
Set the model ID in `.env`:

```env
TOGETHER_API_KEY=your_key
MODEL_ID=<z-image-turbo-model-id-from-together-ai>   # e.g. stabilityai/sdxl-turbo
```

To run against **RunPod** (serverless worker), set instead:

```env
RUNPOD_ENDPOINT_ID=abc123
RUNPOD_API_KEY=your_runpod_key
```

RunPod takes precedence when both `RUNPOD_*` variables are set.

## Docker

```bash
# Build + run
docker-compose up --build

# Run in background
docker-compose up -d

# Logs
docker-compose logs -f api
```

Generated images are stored in a named Docker volume (`moda_ia_storage`)
and survive container restarts.

## Tests

```bash
pytest                         # all tests + coverage
pytest -k test_image_utils     # single module
pytest -k "not ai_client"      # skip AI client tests
pytest --no-cov                # skip coverage
```

### Coverage target: 85 %

| Module | What's tested |
|--------|---------------|
| `test_image_utils.py`      | Resize, EXIF, RGB conversion, base64 round-trip |
| `test_ai_client.py`        | Prompt builders, Together AI & RunPod HTTP mocks, error cases |
| `test_generate_endpoint.py`| All HTTP scenarios via TestClient |
| `test_storage.py`          | Save, count, rolling eviction, path lookup |

## Environment variables

| Variable             | Default | Description |
|----------------------|---------|-------------|
| `TOGETHER_API_KEY`   | —       | Together AI API key (required unless RunPod) |
| `RUNPOD_API_KEY`     | —       | RunPod API key |
| `RUNPOD_ENDPOINT_ID` | —       | RunPod serverless endpoint ID |
| `MODEL_ID`           | `black-forest-labs/FLUX.1-schnell` | Together AI model ID |
| `IMAGE_WIDTH`        | 1024    | Output width (px) |
| `IMAGE_HEIGHT`       | 1024    | Output height (px) |
| `GENERATION_STEPS`   | 4       | Inference steps (4 = Turbo/Schnell) |
| `GUIDANCE_SCALE`     | 3.5     | CFG guidance |
| `STORAGE_DIR`        | storage | Local directory for generated images |
| `MAX_STORED_IMAGES`  | 1000    | Rolling limit per scenario directory |
| `CORS_ORIGINS`       | *       | Comma-separated allowed origins |
| `PORT`               | 8000    | Uvicorn port |
| `MAX_UPLOAD_SIZE_MB` | 10      | Upload limit |

## RunPod deploy

See [`../docs/DEPLOY_RUNPOD.md`](../docs/DEPLOY_RUNPOD.md).

**TL;DR:**

```bash
docker build -t youruser/moda-ia-backend:latest .
docker push youruser/moda-ia-backend:latest
# Then create a Pod on runpod.io with the image and expose port 8000
```
