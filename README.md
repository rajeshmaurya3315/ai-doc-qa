# ⬡ Veda — AI Document & Multimedia Q&A

Veda is a full-stack AI-powered web application that lets you upload PDF documents, audio, and video files — then chat with an AI, get summaries, and navigate audio/video via AI-extracted timestamps.

---

## Features

- **PDF Upload & Chat** — Upload any PDF and ask questions about its content
- **Audio/Video Transcription** — Automatically transcribed via Groq Whisper
- **Timestamp Extraction** — Every audio/video segment gets a start/end timestamp
- **Play Button** — Jump directly to the relevant part of audio/video from chat answers
- **AI Summarization** — 5-point bullet summary of any uploaded document
- **Vector Search** — FAISS semantic search for more accurate context retrieval (optional)
- **Dark UI** — Beautiful, responsive React interface

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python + FastAPI |
| AI/LLM | Groq API (`llama-3.3-70b-versatile`) |
| Transcription | Groq Whisper (`whisper-large-v3`) |
| PDF Parsing | pdfplumber |
| Vector Search | FAISS + sentence-transformers |
| Frontend | React.js + Axios |
| Testing | pytest + pytest-cov (99% coverage) |
| Container | Docker + Docker Compose |
| CI/CD | GitHub Actions |

---

## Project Structure

```
ai-doc-qa/
├── backend/
│   ├── main.py           # FastAPI routes
│   ├── controller.py     # Business logic
│   ├── models.py         # Pydantic models
│   ├── config.py         # Groq client + settings
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env              # GROQ_API_KEY (never commit)
│   └── tests/
│       └── test_main.py  # 99% coverage
├── frontend/
│   ├── src/App.js        # Complete React UI
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── README.md
└── .github/
    └── workflows/
        └── ci-cd.yml
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Groq API key (get free at [console.groq.com](https://console.groq.com))

### Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

Create `.env` in the `backend/` folder:
```
GROQ_API_KEY=gsk_your_key_here
```

Start the server:
```bash
uvicorn main:app --reload
```

Backend runs at: http://localhost:8000

### Frontend

```bash
cd frontend
npm install
npm start
```

Frontend runs at: http://localhost:3000

---

## Docker

```bash
# From project root
docker compose up --build
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/upload` | Upload PDF/audio/video |
| POST | `/chat` | Ask a question about a file |
| POST | `/summarize` | Summarize a file |
| GET | `/documents` | List all uploaded files |
| DELETE | `/documents/{filename}` | Delete a file |
| GET | `/timestamps/{filename}` | Get all timestamps for audio/video |

### Example: Upload
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.pdf"
```

### Example: Chat
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"filename": "document.pdf", "question": "What is this about?"}'
```

### Example: Get Timestamps
```bash
curl http://localhost:8000/timestamps/audio.mp3
```

---

## Testing

```bash
cd backend
pytest tests/ --cov=. --cov-report=term-missing
```

Current coverage: **99%** (16 tests, all passing)

---

## GitHub Actions CI/CD

The pipeline runs automatically on every push to `main`:

1. **Backend Tests** — runs pytest, fails if coverage < 95%
2. **Frontend Build** — runs `npm run build`
3. **Docker Build** — builds images and verifies containers start

### Setup GitHub Secrets

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Value |
|--------|-------|
| `GROQ_API_KEY` | Your Groq API key |

---

## .gitignore

Make sure these are ignored:
```
backend/.env
backend/uploads/
__pycache__/
*.pyc
node_modules/
frontend/build/
```
