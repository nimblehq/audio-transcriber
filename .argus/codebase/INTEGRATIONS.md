# External Integrations

## HuggingFace (PyAnnote)

- **Purpose:** Speaker diarization model access
- **Config:** `HF_TOKEN` env var (required for diarization)
- **Model:** `pyannote/speaker-diarization-3.1`
- **Usage:** `backend/services/transcriber.py` — `DiarizationPipeline`
- **Graceful degradation:** Diarization skipped if `HF_TOKEN` is empty

## WhisperX (Local)

- **Purpose:** Speech-to-text transcription + alignment
- **Source:** `git+https://github.com/m-bain/whisperX.git` (unpinned)
- **Model:** Configurable via `WHISPER_MODEL` (default: `large-v3`)
- **Device:** Auto-detects CUDA, falls back to CPU
- **Usage:** `backend/services/transcriber.py`

## File System Storage

- **Purpose:** All persistence (no database)
- **Location:** `DATA_DIR` env var (default: `./data`)
- **Structure:** `data/meetings/{uuid}/` containing `metadata.json`, `transcript.json`, audio file
- **Templates:** `templates/` directory for analysis prompt templates

## No External Services

- No database (SQLite, PostgreSQL, etc.)
- No message queue (Redis, RabbitMQ, etc.)
- No cloud storage (S3, GCS, etc.)
- No authentication provider
- No CI/CD pipeline configured
