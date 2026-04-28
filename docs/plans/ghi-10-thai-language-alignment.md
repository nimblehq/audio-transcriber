# Plan: Thai Language Alignment

**Story**: ghi-10
**Spec**: docs/specs/transcription-quality-improvements.md (US-3)
**Branch**: feature/10-thai-language-alignment
**Date**: 2026-03-14
**Mode**: Standard — small, focused change with clear test patterns

## Technical Decisions

### TD-1: Custom model_name parameter for Thai
- **Context**: WhisperX does not include Thai in its default alignment model mappings
- **Decision**: Pass `model_name="airesearch/wav2vec2-large-xlsr-53-th"` via a `CUSTOM_ALIGN_MODELS` dict when detected language is Thai
- **Alternatives considered**: Monkey-patching WhisperX's `DEFAULT_ALIGN_MODELS_HF` dict at import time — rejected as fragile

## Files to Create or Modify

- `backend/services/transcriber.py` — Add `"th"` to `ALIGNMENT_LANGUAGES`, add `CUSTOM_ALIGN_MODELS` dict, pass `model_name` to `load_align_model`
- `tests/unit/test_transcriber.py` — Add tests for Thai custom model, unsupported language skip, and English default model

## Approach per AC

### AC 1: Thai (`th`) is recognized as a supported alignment language
Added `"th"` to the `ALIGNMENT_LANGUAGES` set.

### AC 2: Uses `airesearch/wav2vec2-large-xlsr-53-th` alignment model
Created `CUSTOM_ALIGN_MODELS` dict mapping `"th"` to the model name. Passed via `model_name` parameter to `whisperx.load_align_model`.

### AC 3: Model downloaded on first use, not at startup
Already satisfied — alignment models are loaded inside `_run_transcription`, not at import time. HuggingFace downloads on first call.

### AC 4: Unsupported language → alignment skipped gracefully
Already works — the `if detected_language in ALIGNMENT_LANGUAGES` check handles this. Added a test to verify.

### AC 5: Mixed English/Thai → dominant language model used
Already works — WhisperX auto-detect returns the dominant language.

## Commit Sequence

1. Add Thai alignment support to transcriber + tests
2. Persist plan file

## Risks and Trade-offs

- If `airesearch/wav2vec2-large-xlsr-53-th` is removed from HuggingFace, Thai alignment fails at runtime (caught by existing error handling)

## Deviations from Spec

- None

## Deviations from Plan

_None._
