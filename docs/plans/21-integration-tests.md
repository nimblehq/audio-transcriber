# Plan: Integration Tests for API Endpoints

**Story**: #21
**Spec**: docs/specs/test-framework-setup.md (US3)
**Branch**: feature/21-integration-tests
**Date**: 2026-03-14
**Mode**: Standard — testing existing code, TDD not applicable

## Technical Decisions

### TD-1: Mocking start_transcription
- **Context**: POST /api/meetings and POST /api/meetings/{id}/retry spawn daemon threads via start_transcription
- **Decision**: Patch `backend.routers.meetings.start_transcription` in upload/retry tests
- **Alternatives considered**: Letting threads run — would cause side effects and test pollution

### TD-2: Job queue singleton
- **Context**: job_queue is a module-level singleton shared across tests
- **Decision**: Use it directly for setup (creating jobs) and assertions; the in-memory nature makes this straightforward
- **Alternatives considered**: Creating a fresh JobQueue per test — unnecessary complexity given test isolation via tmp_path

### TD-3: Reusing existing conftest fixtures
- **Context**: conftest.py already has client, data_dir, meetings_dir, populated_meeting, sample_audio fixtures
- **Decision**: Reuse existing fixtures, add test-local fixtures only where needed (e.g., processing_meeting for retry tests)
- **Alternatives considered**: Duplicating fixtures — violates DRY

## Files to Create or Modify

- `tests/integration/test_meetings.py` — Integration tests for all meetings router endpoints
- `tests/integration/test_jobs.py` — Integration tests for jobs router endpoint
- `tests/integration/test_analysis.py` — Integration tests for analysis/templates endpoint

## Approach per AC

### AC 1: GET /api/meetings
List meetings, sort order by date desc, empty state returns []

### AC 2: POST /api/meetings
Upload with valid WAV, invalid extension rejected (400), mock start_transcription

### AC 3: GET /api/meetings/{id}
Existing meeting returns metadata+transcript, nonexistent returns 404

### AC 4: PATCH /api/meetings/{id}
Update title, type, speakers; verify persisted changes

### AC 5: PATCH /api/meetings/{id}/segments/speaker
Rename segment speaker, missing segment 404, missing transcript 404

### AC 6: POST /api/meetings/{id}/retry
Retry creates new job, updates status to processing; mock start_transcription

### AC 7: DELETE /api/meetings/{id}
Delete meeting, verify files removed; nonexistent returns 404

### AC 8: GET /api/meetings/{id}/audio
Stream audio file with correct media type; missing file returns 404

### AC 9: GET /api/jobs/{jobId}
Pending/completed/failed job states; nonexistent returns 404

### AC 10: GET /api/templates/{type}
Valid template types return content; invalid type returns 404

## Commit Sequence

1. Add integration tests for meetings endpoints
2. Add integration tests for jobs endpoint
3. Add integration tests for analysis/templates endpoint

## Risks and Trade-offs

- job_queue singleton state may leak between tests if not careful
- start_transcription must always be mocked to avoid spawning real threads

## Deviations from Spec

- Cancel endpoint tests already exist in test_cancel.py (from issue #20), not duplicated here

## Deviations from Plan

_Populated after implementation._
