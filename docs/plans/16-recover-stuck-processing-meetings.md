# Plan: Recover stuck PROCESSING meetings on startup

**Story**: #16
**Spec**: docs/specs/transcription-failure-recovery.md (F1)
**Branch**: feature/16-recover-stuck-processing-meetings
**Date**: 2026-03-14
**Mode**: Standard — simple file I/O logic, straightforward to test after implementation

## Technical Decisions

### TD-1: Separate recovery service module
- **Context**: Recovery logic needs to scan disk and update metadata files
- **Decision**: Create `backend/services/recovery.py` to keep `main.py` clean
- **Alternatives considered**: Inline in `main.py` lifespan — rejected for testability

### TD-2: FastAPI lifespan context manager
- **Context**: Need to run recovery on startup before serving requests
- **Decision**: Use `@asynccontextmanager` lifespan pattern (modern FastAPI)
- **Alternatives considered**: `@app.on_event("startup")` — deprecated in recent FastAPI

## Files to Create or Modify

- `backend/services/recovery.py` — **New**: `recover_stuck_meetings()` function
- `backend/main.py` — Add lifespan context manager wiring recovery on startup
- `tests/unit/test_recovery.py` — **New**: Unit tests for recovery

## Approach per AC

### AC 1: Scan all meeting directories for metadata with status=PROCESSING
Glob `MEETINGS_DIR/*/metadata.json`, load each, check `status` field.

### AC 2: Set status to ERROR with error message
Update matching metadata dicts: `status=error`, `error="Transcription interrupted by app restart"`, write back.

### AC 3: Log each recovered meeting ID
Use `logger.info()` per recovered meeting.

### AC 4: Recovered meetings show retry button in the UI
No UI changes needed — ERROR status already shows the retry button.

## Commit Sequence

1. Add `recover_stuck_meetings` service + unit tests
2. Wire recovery into FastAPI lifespan in `main.py`

## Risks and Trade-offs

- No race condition risk — threads don't survive process restart

## Deviations from Spec

- None anticipated

## Deviations from Plan

_Populated after implementation._
