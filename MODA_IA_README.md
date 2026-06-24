# Moda IA

> Transforme fotos de roupas em imagens profissionais para e-commerce usando IA generativa.

## Visão Geral

O **Moda IA** é um MVP completo que permite a qualquer lojista ou fotógrafo transformar fotos simples de roupas em imagens de qualidade profissional, prontas para uso em lojas virtuais — em segundos.

```
Foto casual da roupa → [IA Generativa] → Imagem profissional de e-commerce
```

## Stack

| Camada    | Tecnologia |
|-----------|-----------|
| Frontend  | Flutter + Material 3 |
| Backend   | FastAPI + Python 3.11 |
| Banco     | Firebase (Auth + Storage) |
| IA        | Together AI / RunPod (SDXL / FLUX) |
| Deploy    | Docker + RunPod |

## Estrutura do Projeto

```
moda-ia/
├── frontend/          # App Flutter
│   ├── lib/
│   │   ├── config/    # Tema e constantes
│   │   ├── models/    # Entidades de dados
│   │   ├── screens/   # Telas (Login, Home, Upload, Result)
│   │   ├── services/  # Auth e API
│   │   └── widgets/   # Componentes reutilizáveis
│   └── pubspec.yaml
│
├── backend/           # API FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/   # Endpoints
│   │   ├── services/  # Lógica de negócio (IA + Firebase)
│   │   ├── models/    # Schemas Pydantic
│   │   └── utils/     # Utilitários de imagem
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
│
└── docs/              # Documentação
    ├── SETUP_BACKEND.md
    ├── SETUP_FRONTEND.md
    └── DEPLOY_RUNPOD.md
```

## Funcionalidades

- **Login Google** via Firebase Authentication
- **Upload de imagem** (câmera ou galeria)
- **4 cenários de fundo:**
  - Fundo branco (e-commerce clássico)
  - Estúdio profissional
  - Loja moderna
  - Lifestyle urbano
- **Geração via IA** (Together AI ou RunPod)
- **Tela de resultado** com comparação antes/depois
- **Download e compartilhamento** da imagem gerada
- **Storage no Firebase** (opcional)

## Início Rápido

### Backend

```bash
cd backend
cp .env.example .env
# Edite .env com sua TOGETHER_API_KEY

docker-compose up --build
# API em http://localhost:8000
# Docs em http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
flutterfire configure --project=seu-projeto-firebase
flutter pub get
flutter run
```

## API

### POST /api/v1/generate

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -F "image=@roupa.jpg" \
  -F "scenario=white_background"
```

**Response:**
```json
{
  "image_url": "https://storage.googleapis.com/...",
  "scenario": "white_background",
  "original_prompt": "professional e-commerce product photo..."
}
```

## Provedores de IA

O backend suporta dois provedores (chaveado por variáveis de ambiente):

| Provedor   | Variáveis                              | Latência |
|------------|----------------------------------------|----------|
| Together AI| `TOGETHER_API_KEY`                     | ~15-30s  |
| RunPod     | `RUNPOD_ENDPOINT_ID` + `RUNPOD_API_KEY`| ~10-20s  |

RunPod tem prioridade quando ambas variáveis estão configuradas.

## Deploy

Ver [docs/DEPLOY_RUNPOD.md](docs/DEPLOY_RUNPOD.md) para instruções completas de deploy no RunPod.

## Licença

MIT
