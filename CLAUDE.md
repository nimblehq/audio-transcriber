# Meeting Transcriber

**Repo:** https://github.com/nimblehq/audio-transcriber

Audio transcription web app using WhisperX + PyAnnote for speaker diarization.

## Tech Stack

- **Backend:** FastAPI (Python), Uvicorn, Pydantic
- **Frontend:** Vanilla JavaScript SPA (no framework)
- **Transcription:** WhisperX (large-v3), PyAnnote (speaker diarization)
- **Storage:** File-based (JSON metadata + audio files, no database)
- **Job system:** In-memory dict with threading (no Celery/Redis)

## Project Structure

```
backend/
  main.py              # FastAPI app, mounts routers + serves SPA
  schemas.py           # Pydantic models (MeetingMetadata, JobInfo, Transcript, etc.)
  routers/
    meetings.py        # CRUD + upload + audio streaming + retry
    jobs.py            # GET /api/jobs/{job_id}
    analysis.py        # GET /api/templates/{type}
  services/
    transcriber.py     # Background thread transcription (_run_transcription)
    job_queue.py       # In-memory JobQueue with thread lock
frontend/
  index.html           # SPA shell, loads all JS/CSS
  css/styles.css       # All styles, dark/light theme via CSS vars
  js/
    app.js             # Client-side router (/, /upload, /meetings/{id})
    api.js             # Fetch wrapper for all API calls
    utils.js           # Formatters, toast, clipboard, speaker colors, escapeHtml
    components/
      meeting-list.js      # List view with status badges
      upload.js            # Drag-drop upload form
      transcript-viewer.js # Audio player, segments, tabs, polling, progress
      speaker-editor.js    # Popover for renaming speakers
      analysis-viewer.js   # LLM prompt generation from templates
config.py              # Env vars: HF_TOKEN, WHISPER_MODEL, DATA_DIR, etc.
run.py                 # Uvicorn entry point (port 8000, reload=True)
transcriber.py         # Standalone CLI transcription script
templates/             # Analysis prompt templates (interview, sales, client, other)
data/meetings/{id}/    # Per-meeting: metadata.json, transcript.json, audio file
```

## Key Flows

**Transcription pipeline:** Upload (POST /api/meetings) -> save audio + metadata.json (status=PROCESSING) -> create JobInfo -> spawn daemon thread -> WhisperX transcribe -> align timestamps -> PyAnnote diarize -> save transcript.json -> update metadata (status=READY)

**Frontend polling:** transcript-viewer.js polls GET /api/jobs/{jobId} every 3s -> shows progress bar -> auto-navigates on completion

**Job states:** PENDING -> PROCESSING -> COMPLETED|FAILED
**Meeting states:** PROCESSING -> READY|ERROR

## API Endpoints

- `GET /api/meetings` - List all (sorted by date desc)
- `POST /api/meetings` - Upload + start transcription (multipart form)
- `GET /api/meetings/{id}` - Meeting detail with transcript
- `PATCH /api/meetings/{id}` - Update title/type/speakers
- `PATCH /api/meetings/{id}/segments/speaker` - Rename single segment speaker
- `POST /api/meetings/{id}/retry` - Retry failed transcription
- `DELETE /api/meetings/{id}` - Delete meeting + files
- `GET /api/meetings/{id}/audio` - Stream audio file
- `GET /api/jobs/{jobId}` - Job progress/status
- `GET /api/templates/{type}` - Analysis prompt template

## Configuration (env vars)

- `HF_TOKEN` - HuggingFace token (required for diarization)
- `WHISPER_MODEL` - Model size (default: large-v3)
- `WHISPER_DEVICE` - Device (default: auto -> cuda or cpu)
- `WHISPER_BATCH_SIZE` - Batch size (default: 16)
- `DATA_DIR` - Data storage path (default: ./data)
- `MAX_UPLOAD_SIZE` - Max file size (default: 500MB)

## Frontend Patterns

- All JS is global (no modules/bundler), loaded via script tags in index.html
- State shared via globals: `currentAudio`, `pollInterval`, `autoScroll`, `window._speakerEditorState`
- Toast notifications via `showToast(message, type)`
- Theme toggle persisted in localStorage
- Recent speaker names persisted in localStorage
- No notification system currently exists
