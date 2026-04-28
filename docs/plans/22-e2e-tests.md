# Plan: E2E Tests for Critical Flows

**Story**: #22
**Spec**: docs/specs/test-framework-setup.md (US4)
**Branch**: feature/22-e2e-tests
**Date**: 2026-03-14
**Mode**: Standard — testing infrastructure, TDD not applicable

## Technical Decisions

### TD-1: E2E vs Integration distinction
- **Context**: Integration tests already cover individual endpoint contracts; E2E tests need to verify multi-step user flows
- **Decision**: E2E tests chain multiple API calls and verify side effects across steps (upload → transcribe → retrieve)
- **Alternatives considered**: Adding to existing integration tests — would blur the distinction and make test intent less clear

### TD-2: Simulating transcription completion
- **Context**: Cannot run actual WhisperX/PyAnnote in tests (BR1 from spec)
- **Decision**: Mock `start_transcription`, then simulate completion by writing transcript.json and updating metadata/job status directly
- **Alternatives considered**: Running a lightweight mock transcriber thread — adds complexity with no benefit

## Files to Create or Modify

- `tests/e2e/test_flows.py` — Four E2E test classes covering upload, transcription completion, retry, and delete flows

## Approach per AC

### Upload flow
POST upload with mocked transcription → verify meeting dir created with metadata.json + audio file → verify job exists in queue

### Transcription completion flow
Upload → simulate transcription by writing transcript.json + updating metadata to READY + marking job COMPLETED → GET meeting → verify transcript returned with segments

### Retry flow
Create ERROR meeting → POST retry → verify new job created → verify status back to PROCESSING

### Delete flow
Upload meeting → DELETE → verify meeting directory removed from disk

## Commit Sequence

1. Add implementation plan for E2E tests
2. Add E2E tests for critical flows

## Risks and Trade-offs

- Some overlap with integration tests is intentional — E2E tests chain multiple steps to verify full workflows

## Deviations from Spec

- Spec US4 mentions polling job status; we verify job state directly since polling is a frontend concern tested by integration tests for the jobs endpoint

## Deviations from Plan

_Populated after implementation._
