# Plan: Provision the diarization PLDA model and surface diarization failures

**Story**: #150
**Spec**: N/A (GitHub issue, bug)
**Branch**: fix/150-provision-diarization-plda
**Date**: 2026-10-27
**Mode**: Standard — `required_repos()`, the `_diarize_and_assign` degrade paths, the worker's metadata write and the retry reset get targeted tests; the ML load/download itself cannot be unit-run.

## Technical Decisions

### TD-1: Pre-fetch `pyannote/speaker-diarization-community-1` during provisioning
- **Context**: pyannote-audio 4.x `SpeakerDiarization.__init__` always loads a PLDA (default checkpoint `pyannote/speaker-diarization-community-1`, subfolder `plda`); `speaker-diarization-3.1`'s config does not override it. The repo is gated. It was not in `required_repos()`, so it downloaded lazily at the diarization step and, for an account that had not accepted its conditions, failed with a 403 that degraded the meeting to all-UNKNOWN speakers.
- **Decision**: Add it to the token-gated repos in `required_repos()` and bump `PROVISIONING_VERSION` 3 → 4, so existing installs re-provision (cached repos are a fast no-op) and a missing access grant surfaces in the setup wizard as the same gated-repo error the other pyannote repos produce.
- **Alternatives considered**: Pass an explicit `plda` to the pipeline from an ungated source — rejected: `whisperx.DiarizationPipeline` does not expose it, and the PLDA is only published in the gated repo. `allow_patterns=["plda/*"]` — rejected: the downloader takes a repo id only, and the repo is small.

### TD-2: Record the diarization failure reason on the meeting
- **Context**: The degrade-to-no-diarization behavior (BR-10, EC-3) is correct, but the reason lived only in `service.log`; the meeting showed `ready` with a single "Unknown" speaker.
- **Decision**: `_diarize_and_assign` returns a third value, a one-line user-facing reason (last non-empty line of the exception — the actionable sentence in huggingface_hub errors — or a timeout message). Both pipelines pass it through, and the worker stores it in a new `MeetingMetadata.diarization_error` (`None` on success or when diarization is disabled by design). Retry clears it. The web viewer and the macOS transcript view show a warning notice with the reason and a re-run action.
- **Alternatives considered**: Marking the meeting `error` — rejected: the transcript is valid and useful without speakers. Storing the reason on the job — rejected: jobs are in-memory and lost on restart.

## Files to Create or Modify

- `backend/services/provisioning.py` — add the repo; bump `PROVISIONING_VERSION` to 4.
- `backend/schemas.py` — `MeetingMetadata.diarization_error`.
- `backend/services/transcriber.py` — return and persist the reason.
- `backend/routers/meetings.py` — clear the reason on retry.
- `frontend/js/components/transcript-viewer.js`, `frontend/css/styles.css` — notice.
- `macos/Sources/MeetingTranscriberKit/Models/Meeting.swift`, `macos/Sources/MeetingTranscriberApp/Views/TranscriptContainerView.swift` — decode + notice.
- Tests: `tests/unit/test_provisioning.py`, `tests/unit/test_transcriber.py`, `tests/integration/test_meetings.py`, `macos/Sources/MeetingTranscriberKitTests/ModelDecodingTests.swift`.
- `CHANGELOG.md` — `[Unreleased] > Fixed`.

## Risks and Trade-offs

- Existing installs re-provision once (v4). Users who never accepted the community-1 conditions now see a provisioning failure instead of silent speaker loss — intended, but it blocks transcription until they accept or clear the token.
- The reason string comes from third-party exception text; it passes through the existing log redaction only for logs, not metadata. huggingface_hub errors do not include the token.

## Deviations

| Date | Story | Decision changed | Rationale |
|------|-------|------------------|-----------|
| 2026-10-30 | #150 | TD-2 / Risks: the diarization failure reason is now passed through `redact_secrets` before it is stored in `metadata.json` and shown in the UI. | PR #151 review: the `status == "error"` branch catches any exception, and a dependency can embed an `hf_` token in its message (see `logging_setup.py`). The plan's assumption that huggingface_hub errors never carry the token did not cover that broad catch, and `metadata.json` ships in the #139 diagnostics zip. |
