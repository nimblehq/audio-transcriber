# Plan: Per-language alignment & speaker assignment for mixed-language meetings

**Story**: #78
**Spec**: docs/specs/multilingual-transcription.md
**Branch**: feature/78-multilingual-alignment-speaker-assignment
**Date**: 2026-06-10
**Mode**: Standard — building on the existing mock-heavy transcriber test pattern; tests written alongside the implementation.

## Technical Decisions

### TD-1: Extract a shared `_diarize_and_assign` helper
- **Context**: The single-language path holds the only diarization + raw-turns-capture + `assign_word_speakers` block (`transcriber.py:301-323`). The multilingual path now needs the identical logic.
- **Decision**: Extract it into `_diarize_and_assign(job_id, audio, num_speakers, device, result, *, progress=70)` returning `(result_with_speakers, diarize_turns)`; no-op `(result, None)` when `HF_TOKEN` is unset. Both paths call it.
- **Alternatives considered**: Duplicate the block into the multilingual path — rejected; it would create the 2nd occurrence and trend toward a rule-of-three violation. Extraction keeps single-language behavior identical (same `progress=70`, same raw-turns capture).

### TD-2: Per-language alignment with a single-language-per-`align()`-call invariant
- **Context**: `whisperx.align` is language-specific. It also **sentence-splits** input segments (output count != input count) and re-builds segment dicts.
- **Decision**: Group segments by detected language and call `whisperx.align` **once per group**. Because each call receives one language's segments, language is re-attached as a **constant** to every returned segment — never positionally zipped. This makes the count mismatch from sentence-splitting harmless and keeps BR-8 (each segment aligned with its own language's model) provably correct.
- **Alternatives considered**: Align all segments in one call and zip language back positionally — rejected; sentence-splitting breaks the 1:1 assumption and would mis-assign languages.

### TD-3: Text-preserving, finite-timestamp guarantees
- **Context**: `whisperx.align` can fail internally (it appends the original segment with `words=[]`), the model can fail to load, and interpolation can leave residual NaN.
- **Decision**: Wrap each group's alignment in `try/except`; on any exception fall back to segment-level timestamps (`_segment_level`, text copied verbatim). Guard empty align output the same way. Run every aligned segment through `_finalize_aligned`, which uses `_finite` to coerce non-finite start/end to a running `last_end` fallback and clamps `end >= start`, yielding finite, non-decreasing timestamps. This satisfies Truth-2 (a missing/failed alignment degrades only timing, never text) for both the "no model configured" and "model present but align failed" cases.
- **Alternatives considered**: Drop NaN/failed segments — rejected; loses transcript text (violates Truth-2).

### TD-4: Coarse progress bumps instead of callback rescaling
- **Context**: `transcribe_multilingual` emits progress up to ~88; alignment + diarization need headroom below the `saving` stage at 90.
- **Decision**: Lower the transcribe cap from `min(pct, 89)` to `min(pct, 80)` inside the `progress_cb`, then fixed bumps — `aligning` at 82, diarize via `_diarize_and_assign(progress=85)`. No rescale arithmetic.
- **Alternatives considered**: Rescale the 20->88 emission into 20->65 — rejected as needless arithmetic with no AC benefit (Architect Minor).

## Files to Create or Modify

- `backend/services/transcriber.py` — add `_finite`, `_segment_level`, `_finalize_aligned`, `_align_multilingual_segments`, `_diarize_and_assign`; rewire `_run_multilingual_transcription` (now aligns + diarizes, takes `num_speakers`, returns `diarize_turns`); update routing in `_run_transcription`.
- `tests/unit/test_transcriber.py` — invert the two obsolete multilingual tests; add per-language alignment, fallback, NaN-repair, unsupported-language, and no-HF_TOKEN tests.
- `docs/plans/78-multilingual-alignment-speaker-assignment.md` — this plan.

## Approach per AC

### AC1: segments grouped by detected language, each group aligned with that language's model
`_align_multilingual_segments` groups by `"language"` and calls `whisperx.align` once per supported language with `model_name=CUSTOM_ALIGN_MODELS.get(language)` (Thai custom model, others default). BR-8 holds via the single-language-per-call invariant.

### AC2: segment whose language has no alignment model retains segment-level timestamps, text unaffected (EC-3, BR-9)
Languages absent from `ALIGNMENT_LANGUAGES` skip `load_align_model` entirely and pass through `_segment_level` — chunk-level start/end, text untouched, no `words` key. The words-less segment still receives a segment-level speaker from `assign_word_speakers` (already proven by the existing single-language unsupported path).

### AC3: clicking a segment jumps to the correct position, highlight tracks
No UI change. Satisfied transitively: `_finalize_aligned` guarantees finite, non-decreasing timestamps and the final list is sorted by start, so the existing player's seek/highlight logic reads coherent values.

## Commit Sequence

1. Extract `_diarize_and_assign` shared helper (single-language behavior unchanged).
2. Add `_align_multilingual_segments` + `_finite`/`_segment_level`/`_finalize_aligned`.
3. Wire alignment + diarization into `_run_multilingual_transcription` + routing.
4. Tests covering AC1/AC2/AC3, truths, and single-language regression.

## Risks and Trade-offs

- `whisperx.align` count/NaN/failure variance — mitigated by count-agnostic iteration, `_finite` repair, and per-group fallback.
- Refactoring the working single-language diarization — mitigated by keeping `progress=70` and asserting `diarize_turns` content is preserved.
- Loading multiple alignment models per meeting increases processing time/memory — accepted per spec OQ-2 (any increase acceptable provided single-language meetings are unaffected).

## Deviations from Spec

- None.

## Deviations from Plan

- None. The implementation followed the approved plan; the only changes from the plan-review negotiation (single-language-per-`align()` invariant, `_finite`/per-group fallback, coarse progress bumps) were already folded into the plan before implementation.
