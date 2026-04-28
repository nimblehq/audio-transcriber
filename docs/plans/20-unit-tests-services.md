# Plan: Unit Tests for Services

**Story**: #20
**Spec**: docs/specs/test-framework-setup.md (US2)
**Branch**: feature/20-unit-tests-services
**Date**: 2026-03-14
**Mode**: Standard — testing existing code, not writing new production code

## Technical Decisions

### TD-1: Mock strategy for _run_transcription
- **Context**: The function lazily imports whisperx, torch, and pyannote inside its body
- **Decision**: Use `unittest.mock.patch` to mock these at their import paths within the function scope, plus mock config module values
- **Alternatives considered**: Installing ML deps in test — too heavy, non-deterministic

### TD-2: Thread safety test for JobQueue
- **Context**: JobQueue uses threading.Lock for concurrency safety
- **Decision**: Use concurrent.futures.ThreadPoolExecutor to verify no exceptions under concurrent access
- **Alternatives considered**: Single-threaded tests only — would not exercise the locking logic

## Files to Create or Modify

- `tests/unit/test_job_queue.py` — new, unit tests for JobQueue class
- `tests/unit/test_transcriber.py` — extend with tests for `_get_device`, `_run_transcription`, `start_transcription`

## Approach per AC

### AC 1: Unit tests for job_queue.py
- create_job returns JobInfo with correct fields and PENDING status
- get_job returns None for unknown ID
- update_job modifies only specified fields and updates timestamp
- update_job silently ignores missing job
- clear removes all jobs
- Thread safety under concurrent create/update operations

### AC 2: Unit tests for transcriber.py
- `_get_device` returns config value when not "auto", detects cuda/cpu when "auto"
- `_run_transcription` happy path: mocked pipeline writes transcript.json, updates metadata to READY
- `_run_transcription` error: sets job to FAILED, writes error to metadata
- `_run_transcription` cancellation: discards results when cancelled mid-run
- `start_transcription` spawns a daemon thread

### AC 3: All tests pass
- Verify with `pytest tests/unit/` from project root

## Commit Sequence

1. Add plan for #20
2. Add unit tests for job_queue.py
3. Add unit tests for transcriber.py (_get_device)
4. Add unit tests for transcriber.py (_run_transcription and start_transcription)

## Risks and Trade-offs

- `_run_transcription` has heavy coupling to module-level config imports — requires careful patching
- Lazy imports inside function body need patching at the right level (builtins.__import__ or sys.modules)

## Deviations from Spec

- Spec US2 includes config.py and schemas.py tests; those are covered by issue #19

## Deviations from Plan

_Populated after implementation._
