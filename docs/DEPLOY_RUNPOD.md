# Deploy no RunPod

## Opção 1 — Serverless (recomendado para MVP)

Use o RunPod Serverless para expor o modelo de IA diretamente, e hospede o FastAPI em outro serviço (Railway, Render, Fly.io, etc.).

### Passo 1: Criar endpoint serverless no RunPod

1. Acesse [RunPod Console](https://www.runpod.io/console/serverless)
2. Clique em **New Endpoint**
3. Selecione o modelo desejado (ex: SDXL, FLUX)
4. Anote o `Endpoint ID`

### Passo 2: Configurar variáveis no backend

```env
RUNPOD_ENDPOINT_ID=abc123xyz
RUNPOD_API_KEY=seu_runpod_api_key
```

Com ambas variáveis definidas, o backend usará RunPod automaticamente.

### Passo 3: Ajustar o payload para seu modelo

Edite `backend/app/services/image_service.py`, função `generate_image_runpod`, para adequar o payload ao handler do seu modelo no RunPod.

Exemplo para SDXL padrão (já configurado):

```python
payload = {
    "input": {
        "prompt": prompt,
        "image": b64_image,
        "width": 1024,
        "height": 1024,
        "num_inference_steps": 30,
    }
}
```

---

## Opção 2 — GPU Pod (backend completo no RunPod)

### Passo 1: Build da imagem Docker

```bash
cd backend
docker build -t moda-ia-api:latest .

# Tag para Docker Hub (necessário para RunPod)
docker tag moda-ia-api:latest seuusuario/moda-ia-api:latest
docker push seuusuario/moda-ia-api:latest
```

### Passo 2: Criar Pod no RunPod

1. Acesse [RunPod Pods](https://www.runpod.io/console/pods)
2. Clique em **Deploy**
3. Configure:
   - **Container Image**: `seuusuario/moda-ia-api:latest`
   - **Container Disk**: 20 GB
   - **GPU**: RTX 4090 ou A100 (para SDXL)
   - **Expose HTTP Ports**: `8000`
4. Em **Environment Variables**, adicione todas as variáveis do `.env`

### Passo 3: Verificar deploy

```bash
curl https://SEU-POD-ID-8000.proxy.runpod.net/health
```

---

## Opção 3 — RunPod Template (automatizado)

Crie um template em `runpod-template.json`:

```json
{
  "name": "Moda IA API",
  "imageName": "seuusuario/moda-ia-api:latest",
  "containerDiskInGb": 20,
  "volumeInGb": 0,
  "ports": "8000/http",
  "env": [
    { "key": "TOGETHER_API_KEY", "value": "{{TOGETHER_API_KEY}}" },
    { "key": "FIREBASE_STORAGE_BUCKET", "value": "{{FIREBASE_STORAGE_BUCKET}}" }
  ]
}
```

---

## CI/CD com GitHub Actions

Adicione `.github/workflows/deploy.yml`:

```yaml
name: Deploy to RunPod

on:
  push:
    branches: [main]
    paths: [backend/**]

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: seuusuario/moda-ia-api:latest
```

---

## Configuração de CORS

Para produção, restrinja o CORS no `.env`:

```env
CORS_ORIGINS=https://app.seudominio.com,https://seudominio.com
```
