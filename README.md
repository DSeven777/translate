# Voice Translator

Real-time voice translation web application.

## Features

- Real-time speech recognition (Whisper)
- Multi-language translation (DeepLX, Google, Baidu, Youdao)
- WebSocket-based real-time communication
- Modern Vue 3 frontend

## Tech Stack

- **Backend**: FastAPI, Whisper, WebSocket
- **Frontend**: Vue 3, Vite
- **Translation**: DeepLX (primary), Google, Baidu, Youdao (fallback)

## Quick Start

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Translation service
TRANSLATOR_PROVIDER=deeplx

# DeepLX
DEEPLX_ENDPOINT=https://api.deeplx.org/translate

# Fallback
TRANSLATOR_FALLBACK_ENABLED=true
TRANSLATOR_FALLBACK_ORDER=["google", "baidu"]
```

## License

MIT
