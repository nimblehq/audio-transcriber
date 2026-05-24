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

**Transcription pipeline:** Upload (POST /api/meetings) -> save audio + metadata.json (status=PROCESSING) -> create JobInfo -> spawn daemon thread -> preprocess audio (if enabled: high-pass filter, noise reduction, loudness normalization) -> WhisperX transcribe -> align timestamps -> PyAnnote diarize -> save transcript.json -> update metadata (status=READY)

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

## Git Workflow

**This repository uses trunk-based development. This section overrides the global "Always follow Gitflow" instruction for all agents and contributors working in this repo.**

- **Trunk:** `main` is the single long-lived branch and the source of truth. There is no `develop` branch.
- **Feature branches:** branch off `main`, named `feature/<issue#>-<slug>` (e.g., `feature/44-trunk-based-development`). Keep them short-lived (target: under a few days).
- **Pull requests:** every change reaches `main` via a PR. Direct pushes to `main` are rejected by branch protection. PR titles follow `[#NN] <description>`.
- **Merging:** squash-merge only. Merge commits and rebase-merges are disabled at the repo level. Linear history is enforced.
- **CI gate:** `Lint & Format` and `Test & Coverage` must pass before a PR is mergeable. Approvals are not required (solo project; CI is the gate).
- **Hotfixes:** use the same flow — short-lived branch off `main`, PR, squash-merge. There is no special hotfix process.
- **Releases:** automated via [`semantic-release`](https://github.com/semantic-release/semantic-release). Every push to `main` runs `.github/workflows/release.yml`, which inspects PRs merged since the last tag and computes the next version from PR labels:
  - `breaking` → major
  - `feature` → minor
  - `bug` → patch
  - any other label (or no label) → no release contribution
  The PR title becomes the release-note entry. When a PR carries multiple release-triggering labels (e.g., `breaking` + `feature`), the highest bump wins: major > minor > patch. Tags use bare semver (e.g., `1.3.0`), with no `v` prefix and no release branch. `CHANGELOG.md` continues to be maintained by hand for now; the auto-generated GitHub Release notes are an additional artifact, not a replacement.
- **PR labels are the release signal — issue labels are not.** Only PR labels affect releases. When opening a PR, pick the label based on the release bump you want, independent of the linked issue's label (they will often match, but don't have to). `.github/workflows/auto-label.yml` applies the right label automatically for branches following `feature/`, `fix/`, `chore/`, `docs/` (and a few synonyms — see the workflow); PRs from arbitrary branch names need a manual label before merge.
- **`breaking` label:** there's no branch prefix for breaking changes. Apply the `breaking` label manually when a PR contains them. Run `scripts/setup-release-labels.sh` once per fresh clone to ensure the label exists.
- **Previewing the next release locally:** `npm ci && GITHUB_TOKEN=$(gh auth token) npx semantic-release --dry-run --no-ci` from a fresh checkout of `main`. The dry-run does not push tags or create releases.
- **`GITHUB_TOKEN` recursion-guard caveat:** the release workflow uses the default `GITHUB_TOKEN`. Per GitHub Actions' default-token recursion guard, the resulting tag and release will **not** trigger other workflows. If future automation needs to react to a new release, switch to a PAT (`GH_TOKEN` secret) and update `release.yml`.
