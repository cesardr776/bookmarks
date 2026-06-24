# Moda IA — Documentação

## Índice

- [Visão Geral](../README.md)
- [Setup do Backend](./SETUP_BACKEND.md)
- [Setup do Frontend](./SETUP_FRONTEND.md)
- [Deploy no RunPod](./DEPLOY_RUNPOD.md)
- [API Reference](#api-reference)

## API Reference

### POST /api/v1/generate

Gera uma imagem profissional a partir de uma foto de roupa.

**Request** (multipart/form-data):

| Campo     | Tipo   | Obrigatório | Descrição |
|-----------|--------|-------------|-----------|
| `image`   | file   | ✅          | Foto da roupa (JPEG/PNG/WebP, máx 10 MB) |
| `scenario`| string | ✅          | Cenário de fundo |
| `prompt`  | string | ❌          | Prompt personalizado |
| `user_id` | string | ❌          | UID do Firebase para storage |

**Cenários disponíveis:**

| Valor | Descrição |
|-------|-----------|
| `white_background` | Fundo branco clean |
| `professional_studio` | Estúdio fotográfico |
| `modern_store` | Loja moderna |
| `urban_lifestyle` | Lifestyle urbano |

**Response** (200 OK):

```json
{
  "image_url": "https://storage.googleapis.com/...",
  "scenario": "white_background",
  "original_prompt": "professional e-commerce product photo..."
}
```

### GET /health

Health check do servidor.

**Response:**

```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```
