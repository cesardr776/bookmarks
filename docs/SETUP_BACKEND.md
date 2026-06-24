# Setup do Backend

## Pré-requisitos

- Python 3.11+
- Docker & Docker Compose
- Conta Together AI ou RunPod
- Projeto Firebase (opcional, para storage)

## Configuração

### 1. Variáveis de ambiente

```bash
cd backend
cp .env.example .env
```

Edite `.env` com suas chaves:

```env
# Together AI (padrão)
TOGETHER_API_KEY=your_key_here

# OU RunPod (sobrescreve Together AI)
RUNPOD_ENDPOINT_ID=abc123
RUNPOD_API_KEY=your_runpod_key
```

### 2. Firebase (opcional)

1. Crie um projeto no [Firebase Console](https://console.firebase.google.com)
2. Ative Authentication > Google
3. Ative Storage
4. Vá em Configurações do Projeto > Contas de Serviço
5. Clique em "Gerar nova chave privada"
6. Salve como `backend/firebase-service-account.json`
7. Configure no `.env`:
   ```env
   FIREBASE_SERVICE_ACCOUNT_PATH=/app/firebase-service-account.json
   FIREBASE_STORAGE_BUCKET=seu-projeto.appspot.com
   ```

## Execução

### Com Docker (recomendado)

```bash
cd backend
docker-compose up --build
```

API disponível em `http://localhost:8000`

### Sem Docker

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Documentação da API

Após iniciar, acesse:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testes

```bash
# Health check
curl http://localhost:8000/health

# Gerar imagem
curl -X POST http://localhost:8000/api/v1/generate \
  -F "image=@/path/to/photo.jpg" \
  -F "scenario=white_background"
```
