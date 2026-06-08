# Plan: Multilingual meeting support — select multiple expected languages

**Story**: #77
**Spec**: docs/specs/multilingual-transcription.md
**Branch**: feature/77-multilingual-language-selection
**Date**: 2026-06-08
**Mode**: Standard — with test-first for the pure language-classification helpers (deterministic, no ML deps); standard for the mock-heavy pipeline wiring.

## Technical Decisions

### TD-1: `expected_languages` as the routing source of truth
- **Context**: The pipeline must choose single- vs multilingual processing, while keeping the existing single-language behavior byte-for-byte for the common case.
- **Decision**: Add `MeetingMetadata.expected_languages: list[str]`. Routing is keyed strictly on `len(expected_languages) >= 2`. `metadata.language` remains the single-path input and is derived: `[]` → `"auto"`, `["xx"]` → `"xx"`, `[2+]` → `"auto"` (single path never runs for 2+).
- **Alternatives considered**: Repurposing the single `language` string (rejected — loses the set; ambiguous routing).

### TD-2: Multilingual path skips alignment and diarization in this slice
- **Context**: Word-level alignment and cross-language speaker accuracy are explicitly a later story (BR-8/BR-9). `assign_word_speakers` needs word timestamps from alignment.
- **Decision**: Multilingual segments keep chunk-level timestamps and `speaker="UNKNOWN"` (the existing no-diarization default). Audio analysis (if enabled) runs via the existing graceful-degradation path with `diarize_turns=None` and `detected_language=dominant`.
- **Alternatives considered**: Bespoke max-overlap speaker assignment (rejected by architect as scope creep + a unique unvalidated code path).

### TD-3: Reproduce WhisperX VAD + faster-whisper detection for per-chunk processing
- **Context**: WhisperX `.transcribe()` assigns one language to the whole file.
- **Decision**: Reproduce WhisperX VAD chunking (guarded import), detect language per chunk via `pipeline.model.detect_language(slice)` constrained to the selected set, transcribe each chunk via `pipeline.model.transcribe(slice, language=lang, vad_filter=False)`.
- **Alternatives considered**: First-pass `.transcribe()` to get chunk boundaries then re-transcribe (rejected — doubles cost, first pass mis-transcribes).

### TD-4: Classification thresholds and dominant-language fallback
- **Decision**: Classify a chunk only if duration ≥ 1.5s AND renormalized-within-set confidence ≥ 0.70 AND raw top prob ≥ 0.5; else fall back to the dominant language. Dominant = duration-weighted argmax over confidently-classified chunks; tie/empty → first of the sorted selected set (deterministic).
- **Context**: Thresholds are heuristic/tunable, not spec-derived.

## Files to Create or Modify

- `backend/schemas.py` — `MeetingMetadata.expected_languages: list[str]` (default `[]`); `TranscriptSegment.language: str | None = None` (None ⇒ fall back to `Transcript.language`, EC-8).
- `backend/routers/meetings.py` — POST accepts `expected_languages: list[str] = Form(default=[])`; sanitize + store; derive `metadata.language`. Replaces old `language` Form param.
- `backend/services/multilingual_transcriber.py` (new) — pure helpers (`_constrained_language`, `_classify_chunk`, `_dominant_language`) + orchestrator `transcribe_multilingual(...)`. Zero ML imports at module top.
- `backend/services/transcriber.py` — route on `len(expected_languages) >= 2`; multilingual branch.
- `frontend/js/components/upload.js` — unchecked checkbox group for languages; collect selected codes.
- `frontend/js/api.js` — `createMeeting(...)` sends one `expected_languages` field per code.
- `frontend/css/styles.css` — checkbox-group styles.
- Tests: `tests/unit/test_schemas.py`, `tests/unit/test_multilingual_transcriber.py` (new), `tests/unit/test_transcriber.py`, `tests/integration/test_meetings.py`.

## Approach per AC

### AC1: Upload form — select zero, one, or many; nothing pre-selected
Checkbox group, none `checked`. Selected codes collected into an array and posted as repeated `expected_languages` fields.

### AC2 / EC-7: Zero or one language → single path unchanged
Router derives `metadata.language`; transcriber branches on `len(expected_languages) >= 2`, so 0/1 runs the untouched single path. Tests assert size-1 calls `load_model(language="xx")` + `transcribe_opts["language"]=="xx"` + align runs + multilingual NOT called.

### AC3: Two+ languages → each chunk transcribed in its detected language from the set
`transcribe_multilingual` VAD-chunks the audio, detects per chunk constrained to the selected set, transcribes each chunk in its final language.

### AC4: Too short/ambiguous chunk → dominant-language fallback
`_classify_chunk` returns None below thresholds; pass-2 assigns the duration-weighted dominant language.

### AC5: Mid-utterance code-switch → whole chunk as its dominant language
One language per chunk by construction (single `transcribe` call per chunk). Accepted limitation.

### AC6: Saved multilingual transcript → every segment records its language
Each segment dict carries `language` = its final language.

### AC7: Retry after selecting 2+ languages → re-processes multilingual
Retry reuses stored `metadata.expected_languages`; no change needed.

## Commit Sequence

1. `[#77]` schemas: expected_languages + per-segment language
2. `[#77]` router: accept/sanitize/derive expected_languages
3. `[#77]` multilingual_transcriber module + unit tests
4. `[#77]` transcriber routing + multilingual branch + tests
5. `[#77]` frontend: upload checkbox multi-select + api + css

## Risks and Trade-offs

- VAD-internals reproduction is pinned to whisperx git-main (guarded import; degrade gracefully).
- Confidence thresholds are heuristic/tunable.
- Multilingual transcripts show `UNKNOWN` speakers until the alignment story lands.

## Deviations from Spec

- None. Speaker accuracy and alignment are intentionally deferred to a later slice, consistent with the spec's story sequencing.

## Deviations from Plan

_Populated after implementation._
