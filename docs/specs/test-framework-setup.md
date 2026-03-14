# Test Framework Setup

## Overview

### Problem Statement

The Meeting Transcriber has zero tests, no test framework, no linting, and no CI/CD pipeline. The app is in production use by the sales team, and changes are merged without any automated quality checks. This creates risk of regressions and makes refactoring unsafe.

### Goals

- Establish a complete backend test framework (unit + integration + E2E)
- Configure linting and formatting with Ruff
- Set up GitHub Actions CI that runs tests and linting on every PR
- Enforce branch protection so CI must pass before merging
- Achieve 80% code coverage target

### Scope

**In scope:**
- Backend test framework (pytest + pytest-asyncio + httpx)
- Unit tests for all services, schemas, and utilities
- Integration tests for all API endpoints
- E2E tests for critical flows (upload -> transcription -> retrieval)
- Linting and formatting (Ruff)
- GitHub Actions CI workflow
- Branch protection rules
- Coverage reporting (pytest-cov)

**Out of scope:**
- Frontend testing (vanilla JS with global state requires refactoring first — separate initiative)
- Performance/load testing
- ML model accuracy testing (WhisperX/PyAnnote output quality)

## User Stories

### US1: Test framework and project structure

As a developer, I want a configured test framework so that I can write and run tests locally with a single command.

- pytest configured with pytest-asyncio and httpx TestClient
- `tests/` directory with `unit/`, `integration/`, and `e2e/` subdirectories
- Shared fixtures in `tests/conftest.py` (test client, temp data directory, sample files)
- Test fixtures directory (`tests/fixtures/`) with sample metadata.json, transcript.json, and a minimal audio file
- `pytest.ini` or `pyproject.toml` section with sensible defaults
- Tests runnable via `pytest` from project root

### US2: Unit tests for backend services and schemas

As a developer, I want unit tests covering business logic so that I can refactor with confidence.

- Unit tests for `backend/schemas.py` (Pydantic model validation, serialization, enum values)
- Unit tests for `backend/services/job_queue.py` (add, get, update, thread safety)
- Unit tests for `backend/services/transcriber.py` with WhisperX/PyAnnote mocked (verify correct call sequence, output processing, error handling, status updates)
- Unit tests for `config.py` (default values, env var overrides)

### US3: Integration tests for API endpoints

As a developer, I want integration tests for all API endpoints so that I can verify request/response contracts.

- Tests for all endpoints in `backend/routers/meetings.py`:
  - `GET /api/meetings` — list meetings, sort order, empty state
  - `POST /api/meetings` — upload with valid file, invalid file type, missing fields, oversized file
  - `GET /api/meetings/{id}` — existing meeting, non-existent meeting (404)
  - `PATCH /api/meetings/{id}` — update title, type, speakers
  - `PATCH /api/meetings/{id}/segments/speaker` — rename speaker in segment
  - `POST /api/meetings/{id}/retry` — retry failed transcription
  - `DELETE /api/meetings/{id}` — delete meeting and verify file cleanup
  - `GET /api/meetings/{id}/audio` — stream audio, missing file (404)
- Tests for `backend/routers/jobs.py`:
  - `GET /api/jobs/{jobId}` — pending, processing, completed, failed states; non-existent job (404)
- Tests for `backend/routers/analysis.py`:
  - `GET /api/templates/{type}` — valid types, invalid type (404)
- All tests use file system isolation via `tmp_path`
- Transcription service mocked in upload tests (no actual ML processing)

### US4: E2E tests for critical flows

As a developer, I want E2E tests for the main user flows so that I can verify the system works end-to-end.

- Upload flow: POST upload -> verify files created on disk -> verify metadata.json content -> verify job created
- Transcription completion flow: mock transcription completing -> verify transcript.json written -> verify metadata status updated to READY -> verify GET meeting returns transcript
- Retry flow: simulate failed transcription -> POST retry -> verify new job created
- Delete flow: upload meeting -> DELETE -> verify files removed from disk

### US5: Linting and formatting with Ruff

As a developer, I want automated linting and formatting so that code style is consistent across the team.

- Ruff configured in `pyproject.toml` with sensible rule set (E, F, I, W at minimum)
- Format configuration (line length, quote style) defined
- All existing code passes linting (fix existing violations as part of setup)
- Runnable via `ruff check .` and `ruff format --check .`

### US6: GitHub Actions CI workflow

As a developer, I want CI to run automatically on PRs so that quality issues are caught before merge.

- Workflow file at `.github/workflows/ci.yml`
- Triggers on pull requests to `develop` and `main`
- Steps: checkout, Python setup, install dependencies, run Ruff check, run Ruff format check, run pytest with coverage
- Coverage report generated and printed to stdout (no external service needed)
- Fail the workflow if coverage drops below 80%
- Fail the workflow if linting or formatting checks fail

### US7: Branch protection

As a developer, I want branch protection rules so that broken code cannot be merged.

- Branch protection on `develop`: require CI workflow to pass before merging
- Document the branch protection setup steps (manual GitHub settings configuration)

## Business Rules

| ID | Rule | Rationale |
|----|------|-----------|
| BR1 | WhisperX and PyAnnote must be mocked in all automated tests | Models are slow (minutes per run), require specific hardware (MPS/CUDA), and produce non-deterministic output |
| BR2 | Each test must use isolated file system state via `tmp_path` | Prevents test pollution; the app uses file-based storage so isolation is critical |
| BR3 | Coverage threshold is 80% enforced in CI | Ensures meaningful coverage without chasing diminishing returns on ML pipeline internals |
| BR4 | Ruff is the single tool for both linting and formatting | Replaces flake8 + isort + black with one fast tool, reducing config complexity |
| BR5 | CI runs on PRs only, not on every push to feature branches | Keeps CI costs reasonable for a small team |

## Data Requirements

### Test fixtures needed

| Fixture | Description |
|---------|-------------|
| `tests/fixtures/sample.wav` | Minimal valid WAV file (< 1 second silence) for upload tests |
| `tests/fixtures/metadata.json` | Sample MeetingMetadata in READY state |
| `tests/fixtures/metadata_processing.json` | Sample MeetingMetadata in PROCESSING state |
| `tests/fixtures/metadata_error.json` | Sample MeetingMetadata in ERROR state |
| `tests/fixtures/transcript.json` | Sample Transcript with 3-4 segments, 2 speakers |

### Dependencies to add

| Package | Purpose |
|---------|---------|
| `pytest` | Test runner |
| `pytest-asyncio` | Async test support for FastAPI |
| `httpx` | TestClient for FastAPI (ASGI) |
| `pytest-cov` | Coverage reporting |
| `ruff` | Linting and formatting |

## Edge Cases

| ID | Scenario | Expected Behavior |
|----|----------|-------------------|
| EC1 | Test runs on machine without WhisperX/PyAnnote installed | Tests pass because ML models are fully mocked |
| EC2 | CI runs without HF_TOKEN env var | Tests pass because diarization is mocked; config tests use env var overrides |
| EC3 | Tests run concurrently (pytest-xdist, future) | Each test has its own `tmp_path`, so no conflicts |
| EC4 | Audio file fixtures in git | Use minimal file (< 1KB) to avoid bloating the repo |
| EC5 | Existing code has Ruff violations | Fix all violations as part of the initial setup, not as a separate PR |

## Open Questions

| ID | Question | Impact |
|----|----------|--------|
| OQ1 | Should we add `pytest-xdist` for parallel test execution from the start? | Faster CI runs, but adds complexity; may not be needed until the test suite grows |
| OQ2 | Should coverage reports be posted as PR comments (e.g., via codecov or a GH Action)? | Better visibility but adds external dependency; stdout report may suffice initially |
