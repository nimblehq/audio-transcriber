# Plan: Test Framework Setup

**Story**: #19
**Spec**: docs/specs/test-framework-setup.md
**Branch**: feature/19-test-framework-setup
**Date**: 2026-03-14
**Mode**: Standard — setting up the test framework itself, TDD not applicable

## Technical Decisions

### TD-1: config.py testing
- **Context**: config.py executes at import time (load_dotenv, MEETINGS_DIR.mkdir)
- **Decision**: Use monkeypatch + importlib.reload to test env var overrides with tmp_path isolation
- **Alternatives considered**: Refactoring config.py to be lazy — out of scope for this story

### TD-2: sample.wav fixture
- **Context**: Need a valid WAV file for upload tests, must be <1KB (T4)
- **Decision**: Commit a ~78-byte WAV file (44-byte header + minimal PCM data)
- **Alternatives considered**: Generate at runtime in conftest — adds complexity, fixture file is simpler

### TD-3: TestClient approach
- **Context**: FastAPI with async endpoints needs async-capable test client
- **Decision**: Use httpx.AsyncClient with ASGITransport, patching DATA_DIR to tmp_path
- **Alternatives considered**: Synchronous TestClient — would not support async endpoints

## Files to Create or Modify

- `requirements.txt` — add pytest, pytest-asyncio, httpx, pytest-cov
- `pyproject.toml` — pytest configuration section
- `tests/__init__.py` — package marker
- `tests/conftest.py` — shared fixtures (TestClient, tmp data dir, fixture loaders)
- `tests/unit/__init__.py` — package marker
- `tests/unit/test_schemas.py` — unit tests for schemas.py
- `tests/unit/test_config.py` — unit tests for config.py
- `tests/integration/__init__.py` — package marker
- `tests/e2e/__init__.py` — package marker
- `tests/fixtures/sample.wav` — minimal WAV file
- `tests/fixtures/metadata.json` — READY state
- `tests/fixtures/metadata_processing.json` — PROCESSING state
- `tests/fixtures/metadata_error.json` — ERROR state
- `tests/fixtures/transcript.json` — 3-4 segments, 2 speakers

## Approach per AC

### AC 1: Dev dependencies
Add pytest, pytest-asyncio, httpx, pytest-cov to requirements.txt

### AC 2: Directory structure
Create tests/ with unit/, integration/, e2e/ subdirs and __init__.py files

### AC 3: conftest.py with shared fixtures
FastAPI TestClient, tmp data dir, sample file loaders

### AC 4: Test fixtures
sample.wav (<1KB), metadata JSONs (3 states), transcript.json

### AC 5: pyproject.toml pytest config
testpaths, asyncio_mode=auto, coverage settings

### AC 6: Unit tests for schemas.py and config.py
Model validation, serialization, enum values, defaults, env var overrides

### AC 7: All tests pass from project root
Verify with pytest command

## Commit Sequence

1. Add dev dependencies and pyproject.toml pytest config
2. Add test directory structure and fixture files
3. Add conftest.py with shared fixtures
4. Add unit tests for schemas.py
5. Add unit tests for config.py

## Risks and Trade-offs

- config.py module-level side effects require careful reload handling in tests
- No existing pyproject.toml — creating one solely for pytest config

## Deviations from Spec

- Spec US2 includes job_queue and transcriber tests; issue scopes to schemas/config only

## Deviations from Plan

_Populated after implementation._
