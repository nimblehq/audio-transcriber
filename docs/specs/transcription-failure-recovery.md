# Transcription Failure Recovery

## Problem

When transcription fails or gets stuck, meetings remain in PROCESSING status permanently. Users must delete the meeting and re-upload the audio file, losing any metadata (title, type, speaker names) they already entered. This is the top user friction point.

### Root Causes

1. **Stuck PROCESSING state** — If the transcription thread hangs or dies without raising an exception, the meeting status never transitions to ERROR. The retry button only appears for ERROR status, so stuck meetings have no recovery path.
2. **Job state lost on restart** — Job tracking is in-memory only. Restarting the app leaves PROCESSING meetings orphaned with no thread running.
3. **No timeout** — Transcription threads can hang indefinitely with no watchdog.

## Solution

### F1: Detect and recover stuck transcriptions on startup

On app startup, scan all meetings with PROCESSING status. Since job state is in-memory and lost on restart, any PROCESSING meeting at startup has no active thread — transition it to ERROR so the existing retry mechanism can handle it.

**Acceptance criteria:**
- On app startup, all meetings with status=PROCESSING are set to status=ERROR
- These meetings show the retry button in the UI
- Retrying a recovered meeting works end-to-end

### F2: Manual unstuck from the UI

Allow users to force a stuck PROCESSING meeting to ERROR state directly from the meeting detail view, without restarting the app.

**Acceptance criteria:**
- PROCESSING meetings show a "Cancel transcription" button after a reasonable delay (e.g., visible after 5 minutes, or always visible)
- Clicking it sets the meeting status to ERROR and kills/abandons the transcription job
- The retry button appears immediately after cancelling
- Confirmation prompt before cancelling ("Are you sure? This will stop the current transcription.")

### F3: Transcription timeout with error transition

Add a configurable timeout (default: 30 minutes) for transcription jobs. If a transcription exceeds the timeout, mark the job as FAILED and the meeting as ERROR.

**Acceptance criteria:**
- Transcriptions that exceed the timeout are marked ERROR
- Timeout is configurable via `TRANSCRIPTION_TIMEOUT` env var (default: 1800 seconds)
- The retry button appears for timed-out meetings
- Timeout value is logged when a transcription is killed

### F4: Preserve metadata on retry

When retrying a transcription, keep the existing meeting metadata (title, type, speaker names) intact. Only reset the status and job reference.

**Acceptance criteria:**
- Retrying a failed transcription preserves title, meeting_type, and speaker names
- Only status and job_id fields are updated on retry
- The audio file is not re-uploaded or duplicated

### F5: Surface failure reason in the UI

Ensure the meeting detail view shows the retry button for any meeting in ERROR state, with a message indicating what went wrong.

**Acceptance criteria:**
- ERROR meetings show a retry button (already exists, verify it works)
- Error message indicates the failure reason when available (e.g., "Transcription timed out", "Transcription failed: {error}", "Transcription cancelled by user")
- Meeting list shows ERROR status badge (not stuck on PROCESSING)

## Out of Scope

- Persistent job queue (Redis/database) — overkill for local single-user app
- Automatic retry without user action
- Model caching across jobs — not impactful for current usage pattern (~2-10 meetings/week)
- Concurrent transcription limits — users rarely upload multiple files at once

## Technical Notes

- F1 implementation belongs in `backend/main.py` as a startup event/lifespan handler
- F2 needs a new endpoint (e.g., `POST /api/meetings/{id}/cancel`) and a UI button in transcript-viewer.js
- F3 can use `threading.Timer` or a simple timestamp check in the transcription thread
- F4 requires auditing `retry_transcription()` in `backend/routers/meetings.py` to ensure it doesn't overwrite metadata fields
- The existing retry endpoint and UI button are functional — the core issue is meetings never reaching ERROR state
