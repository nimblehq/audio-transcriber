# Architecture

## Pattern

**Monolithic SPA + API server** — single FastAPI process serves both the REST API and the static frontend. No microservices, no reverse proxy.

## Data Flow

```
Upload (multipart POST)
  → Save audio file to disk
  → Write metadata.json (status=PROCESSING)
  → Create in-memory JobInfo
  → Spawn daemon thread
    → WhisperX transcribe
    → WhisperX align timestamps
    → PyAnnote diarize speakers
    → Write transcript.json
    → Update metadata.json (status=READY)
  → Return job_id to client

Frontend polls GET /api/jobs/{jobId} every 3s
  → Shows progress bar
  → Auto-navigates on completion
```

## Concurrency Model

- **Background threads** — each transcription runs in a daemon thread (`threading.Thread`)
- **In-memory job queue** — `JobQueue` singleton with thread lock for status tracking
- **No concurrency limit** — unbounded thread creation per upload
- **No persistence** — all job state lost on restart

## Key Abstractions

- **Pydantic models** (`backend/schemas.py`) — `MeetingMetadata`, `Transcript`, `JobInfo`, enums for statuses
- **JobQueue** (`backend/services/job_queue.py`) — singleton, thread-safe dict wrapper
- **Router modules** (`backend/routers/`) — FastAPI routers for meetings, jobs, analysis
- **Client-side router** (`frontend/js/app.js`) — hash/path-based SPA routing

## API Design

RESTful JSON API under `/api/` prefix. Catch-all route serves `index.html` for SPA client-side routing. Static assets served from `/static/` mount.

## State Management

- **Server:** File system (JSON files) + in-memory job dict
- **Client:** Global variables, localStorage for theme and recent speaker names
