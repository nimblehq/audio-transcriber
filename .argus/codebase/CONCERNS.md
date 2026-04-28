# Concerns & Technical Debt

## Security

- **No authentication/authorization** — all endpoints are publicly accessible
- **Path traversal risk** — meeting IDs used directly in file paths without sanitization (`backend/routers/meetings.py`)
- **Unsafe model loading** — `torch.load` with `weights_only=False` in transcriber
- **Large uploads buffered in RAM** — entire files (up to 500MB) held in memory during upload
- **No CORS or rate limiting** configured

## Scalability

- **In-memory job queue** — no persistence, no cleanup; jobs lost on restart (`backend/services/job_queue.py`)
- **No concurrency limit** on transcription threads — each upload spawns a daemon thread
- **Model reloaded per job** — WhisperX model loaded fresh for each transcription (`backend/services/transcriber.py`)
- **O(n) directory scan** — meeting listing scans all directories on every request

## Data Integrity

- **No file locking** between API endpoints and background transcription threads
- **No atomic writes** — partial writes possible on crash
- **Delete during transcription** — deleting a meeting while transcription is active causes errors

## Dependencies

- **Unpinned versions** in `requirements.txt`
- **WhisperX installed from git HEAD** — no version pinning, breaking changes possible

## Technical Debt

- **Zero tests** — no test framework, no test files, no CI testing
- **Duplicate transcriber scripts** — `transcriber.py` (root) and `backend/services/transcriber.py`
- **Silent error swallowing** — broad exception catches with no logging in several places
- **Catch-all SPA route** — masks API typos by returning `index.html` for unmatched routes

## Key Files

- `backend/main.py` — app setup
- `backend/routers/meetings.py` — CRUD endpoints
- `backend/services/transcriber.py` — background transcription
- `backend/services/job_queue.py` — in-memory job tracking
- `config.py` — env var configuration
- `requirements.txt` — dependency list
