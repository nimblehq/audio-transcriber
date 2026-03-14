# Plan: Cancel stuck transcription from the UI

**Story**: #17
**Spec**: docs/specs/transcription-failure-recovery.md — F2
**Branch**: feature/17-cancel-stuck-transcription
**Date**: 2026-03-14
**Mode**: TDD — pytest + httpx test client available with fixtures

## Technical Decisions

### TD-1: Add error field to MeetingMetadata
- **Context**: Story requires storing "Transcription cancelled by user" message
- **Decision**: Add `error: str | None = None` to MeetingMetadata
- **Alternatives considered**: Storing error only in JobInfo (but metadata persists across restarts, jobs don't)

### TD-2: Mark-and-ignore for thread cancellation
- **Context**: Python threads can't be killed cleanly
- **Decision**: Mark job as FAILED, let thread finish, check status before writing results
- **Alternatives considered**: Using multiprocessing (overkill), threading.Event (requires plumbing through WhisperX calls)

## Files to Create or Modify

- `backend/schemas.py` — Add `error` field to MeetingMetadata
- `backend/routers/meetings.py` — Add `POST /api/meetings/{id}/cancel` endpoint
- `backend/services/transcriber.py` — Add `_is_cancelled()` check before saving results
- `frontend/js/api.js` — Add `cancelTranscription()` method
- `frontend/js/components/transcript-viewer.js` — Cancel button + error message display
- `frontend/css/styles.css` — Cancel button styling
- `tests/unit/test_transcriber.py` — Tests for `_is_cancelled()`
- `tests/integration/test_cancel.py` — Integration tests for cancel endpoint
- `tests/fixtures/metadata_error.json` — Add error field to fixture

## Approach per AC

### AC 1: New endpoint POST /api/meetings/{id}/cancel
Load metadata, verify PROCESSING status (409 otherwise), set status=ERROR, error message, mark job FAILED.

### AC 2: PROCESSING meetings show Cancel button
Render cancel button in the processing state section of transcript-viewer.js.

### AC 3: Confirmation dialog before cancelling
Use `confirm()` before calling the cancel API.

### AC 4: After cancelling, retry button appears
Re-navigate to the meeting view which re-renders with ERROR state showing retry button.

### AC 5: Error message set to "Transcription cancelled by user"
Set in cancel endpoint, displayed in error state UI.

### AC 6: API method added to api.js
Add `cancelTranscription(id)` to the API object.

### AC 7: Transcriber checks job status before writing results
Add `_is_cancelled()` that reads metadata.json and checks if status is still PROCESSING.

## Commit Sequence

1. Add error field to MeetingMetadata schema + tests + fixture update
2. Add cancel endpoint + integration tests
3. Add cancellation check in transcriber + unit tests
4. Add frontend cancel button, API method, error display

## Risks and Trade-offs

- Race condition between thread finishing and user cancelling is mitigated by the status check, but there's a small window where both could write metadata simultaneously. Acceptable for single-user app.
- The cancelled thread continues consuming resources until it finishes naturally.

## Deviations from Spec

- Spec mentions "visible after 5 minutes, or always visible" — chose always visible for simplicity, since the user explicitly wants to cancel.

## Deviations from Plan

_None._
