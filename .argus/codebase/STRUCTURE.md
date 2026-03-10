# Project Structure

```
.
├── run.py                        # Entry point: Uvicorn server (port 8000, reload)
├── config.py                     # Env var configuration (HF_TOKEN, paths, model settings)
├── transcriber.py                # Standalone CLI transcription script (duplicate)
├── requirements.txt              # Python dependencies
├── backend/
│   ├── main.py                   # FastAPI app setup, mounts routers + serves SPA
│   ├── schemas.py                # Pydantic models and enums
│   ├── routers/
│   │   ├── meetings.py           # CRUD, upload, audio streaming, retry
│   │   ├── jobs.py               # GET /api/jobs/{job_id}
│   │   └── analysis.py           # GET /api/templates/{type}
│   └── services/
│       ├── transcriber.py        # Background thread transcription pipeline
│       └── job_queue.py          # In-memory JobQueue singleton
├── frontend/
│   ├── index.html                # SPA shell, loads all JS/CSS
│   ├── css/
│   │   └── styles.css            # All styles, dark/light theme via CSS vars
│   └── js/
│       ├── app.js                # Client-side router (/, /upload, /meetings/{id})
│       ├── api.js                # Fetch wrapper for all API calls
│       ├── utils.js              # Formatters, toast, clipboard, speaker colors
│       └── components/
│           ├── meeting-list.js   # List view with status badges
│           ├── upload.js         # Drag-drop upload form
│           ├── transcript-viewer.js  # Audio player, segments, tabs, polling
│           ├── speaker-editor.js     # Popover for renaming speakers
│           └── analysis-viewer.js    # LLM prompt generation from templates
├── templates/                    # Analysis prompt templates (interview, sales, etc.)
├── data/meetings/{id}/           # Per-meeting storage
│   ├── metadata.json
│   ├── transcript.json
│   └── <audio file>
└── .github/
    └── PULL_REQUEST_TEMPLATE.md
```

## Entry Points

- **Server:** `run.py` → `backend/main.py` (FastAPI app)
- **Frontend:** `frontend/index.html` (served by FastAPI)
- **CLI:** `transcriber.py` (standalone, not used by server)

## Adding New Code

- **New API endpoint:** Add to existing router in `backend/routers/` or create new router and mount in `backend/main.py`
- **New Pydantic model:** Add to `backend/schemas.py`
- **New frontend component:** Add JS file in `frontend/js/components/`, load via `<script>` in `index.html`
- **New service:** Add to `backend/services/`
