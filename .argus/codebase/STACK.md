# Tech Stack

## Languages

- **Python 3.12** — Backend, transcription pipeline
- **JavaScript (ES6)** — Frontend SPA (vanilla, no framework)
- **HTML/CSS** — Frontend markup and styling

## Backend Framework

- **FastAPI** >= 0.115.0 — async web framework
- **Uvicorn** >= 0.34.0 — ASGI server with hot reload
- **Pydantic** — data validation (via FastAPI)
- **python-multipart** >= 0.0.20 — file upload handling
- **python-dotenv** >= 1.0.0 — env var loading

## ML / Transcription

- **WhisperX** — speech-to-text (installed from git HEAD, unpinned)
- **PyTorch** (`torch`, `torchaudio`) — ML runtime, unpinned
- **PyAnnote** (`pyannote/speaker-diarization-3.1`) — speaker diarization via HuggingFace

## Frontend

- Vanilla JavaScript SPA — no build step, no bundler, no framework
- Global script loading via `<script>` tags in `index.html`
- CSS custom properties for dark/light theme

## Package Management

- **pip** with `requirements.txt` (no poetry/pipenv)
- **npm** — only for dev tooling (`argus-monorepo` devDependency)
- Python virtualenv at `.venv/` and `lib/`

## Runtime

- Python 3.12
- No containerization (Dockerfile absent)
- Dev server: `run.py` → Uvicorn on port 8000 with reload

## Build Tools

- None — no build step for frontend or backend
- No linter, formatter, or type checker configured
