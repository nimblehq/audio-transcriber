# Plan: Per-segment emotion gating for mixed-language meetings

**Story**: 80
**Spec**: docs/specs/multilingual-transcription.md
**Branch**: feature/80-multilingual-emotion-per-segment
**Date**: 2026-06-10
**Mode**: TDD — pure partition logic with clear inputs/outputs and an existing test harness (`TestRunAudioAnalysis`).

## Technical Decisions

### TD-1: Per-segment gating lives in `_run_emotion_analysis`, not the analyzer
- **Context**: The whole-meeting gate (`detected_language != "en"`) must become per-segment. The gate could live in the analyzer or the transcriber call site.
- **Decision**: Keep the gate in `transcriber._run_emotion_analysis` (the slice scope says "replace the gate in that function"). The analyzer stays generic — it classifies whatever segments it is given.
- **Alternatives considered**: Pushing language awareness into `emotion_analyzer.analyze_segments` and its `_Segment` protocol — rejected as wider blast radius and the analyzer's protocol has no `language`.

### TD-2: `SUPPORTED_LANGUAGES` constant owned by the emotion analyzer
- **Context**: "en" was hardcoded in the gate. Need a single source of truth.
- **Decision**: `SUPPORTED_LANGUAGES = frozenset({"en"})` in `emotion_analyzer.py` (the model is the authority on what it supports); imported by the transcriber.
- **Alternatives considered**: Constant in transcriber — rejected; analyzer is the right home. Thai SER model is explicitly out of scope (OQ-4).

### TD-3: Mirror the prosody unavailable-marker pattern
- **Context**: "Non-English segments are marked unavailable." Prosody already has `ProsodyUnavailable` + `AudioAnalysis.prosody_unavailable` (data-only markers, never rendered).
- **Decision**: Add `EmotionUnavailable(segment_id, reason)` and `AudioAnalysis.emotion_unavailable`. Frontend needs no badge work (no-annotation → no-badge is already graceful).

### TD-4: Effective-language fallback for EC-8 backward compatibility
- **Context**: Single-language and pre-feature segments carry `language=None`.
- **Decision**: Effective language `lang = seg.language or detected_language`. This preserves today's behavior: an English single-language meeting analyzes every segment; a French one marks every segment unavailable with reason `language_not_supported:fr`.

## Files to Create or Modify

- `backend/services/emotion_analyzer.py` — add `SUPPORTED_LANGUAGES = frozenset({"en"})`.
- `backend/schemas.py` — add `EmotionUnavailable` model; add `emotion_unavailable` field to `AudioAnalysis`.
- `backend/services/transcriber.py` — rewrite `_run_emotion_analysis` (4-tuple return with per-segment markers); update `_run_audio_analysis` to unpack and populate `emotion_unavailable`.
- `frontend/js/components/upload.js` — correct the disclosure copy.
- `tests/unit/test_transcriber.py`, `tests/unit/test_schemas.py` — coverage.

## Approach per AC

### AC 1: English segments annotated, non-English marked unavailable, meeting not skipped
Partition `segment_models` by effective language. Supported → analyzed subset; unsupported → `EmotionUnavailable`. Non-empty supported list → `analyze_segments(subset)` → `COMPLETED` + markers. The analyzer slices audio by absolute `start/end`, so a subset over the full audio array is safe.

### AC 2: No English → unavailable (not failed), prosody and interaction still run
Empty supported list → `UNAVAILABLE` (never `FAILED`), reason `language_not_supported:<sorted,unique,langs>`. Prosody/interaction untouched; `_roll_up_status` completes overall.

### AC 3: Prosody and interaction identical regardless of per-segment language
`_run_prosody_analysis` and `_run_interaction_analysis` unchanged.

## Commit Sequence

1. `[#80]` schema (`EmotionUnavailable` + field) and `SUPPORTED_LANGUAGES` constant
2. `[#80]` per-segment gating in transcriber + tests
3. `[#80]` upload disclosure copy

## Risks and Trade-offs

- Return-type change to 4-tuple is contained in `transcriber.py`; external tests call `_run_audio_analysis`, not the tuple directly. The FAILED branch still returns its accumulated markers.

## Deviations from Spec

- None.

## Deviations from Plan

_Populated after implementation._
