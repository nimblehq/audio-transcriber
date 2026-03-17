# Plan: Audio Preprocessing

**Story**: #13
**Spec**: `docs/specs/transcription-quality-improvements.md` — US-1
**Branch**: `feature/13-audio-preprocessing`
**Date**: 2026-03-14
**Mode**: Standard — core logic is straightforward audio/numpy operations

## Technical Decisions

### TD-1: Preprocessing as a separate service module
- **Context**: Preprocessing is a distinct pipeline stage
- **Decision**: New `backend/services/audio_preprocessor.py`
- **Alternatives considered**: Inline in transcriber.py — rejected for separation of concerns

### TD-2: Preprocessed file stored alongside original as WAV
- **Context**: Original must be preserved (T3); preprocessed audio needs to be on disk for WhisperX
- **Decision**: Save as `audio_preprocessed.wav` in meeting directory, clean up after transcription
- **Alternatives considered**: In-memory numpy array — rejected because WhisperX `load_audio` expects a file path

## Files to Create or Modify

- `backend/services/audio_preprocessor.py` — new: high-pass filter, noise reduction, loudness normalization
- `backend/schemas.py` — add `preprocess_audio: bool = True` to MeetingMetadata
- `backend/routers/meetings.py` — accept `preprocess_audio` form field
- `backend/services/transcriber.py` — call preprocessor, use preprocessed audio path
- `frontend/js/components/upload.js` — add preprocessing toggle checkbox
- `frontend/js/api.js` — pass `preprocess_audio` in createMeeting
- `requirements.txt` — add noisereduce and pyloudnorm
- `tests/unit/test_audio_preprocessor.py` — new: unit tests
- `tests/integration/test_meetings.py` — test preprocess_audio persistence

## Approach per AC

### AC 1: Audio undergoes preprocessing (high-pass, noise reduction, loudness normalization)
Load audio with soundfile, apply 80Hz butterworth high-pass (scipy), noisereduce with prop_decrease=0.75 (T1/BR-3), pyloudnorm to -23 LUFS. Save as WAV working copy.

### AC 2: Preprocessing enabled by default
`preprocess_audio` field defaults to `True` in MeetingMetadata.

### AC 3: Upload form toggle to disable preprocessing
Checkbox in upload form, checked by default.

### AC 4: Conservative noise reduction doesn't degrade clean audio
Enforced by prop_decrease=0.75 setting.

### AC 5: `preprocess_audio` field persisted in MeetingMetadata
New Pydantic field with default True.

### AC 6: New dependencies
Add noisereduce>=3.0.0 and pyloudnorm>=0.1.1 to requirements.txt.

## Commit Sequence

1. Add preprocess_audio field to schema + requirements
2. Add audio_preprocessor.py service
3. Wire preprocessor into transcription pipeline
4. Add preprocess_audio to upload endpoint
5. Add preprocessing toggle to frontend
6. Add tests

## Risks and Trade-offs

- soundfile and scipy are transitive deps of whisperx — no explicit addition needed
- Preprocessed file is always WAV regardless of input format

## Deviations from Spec

- None anticipated

## Deviations from Plan

_Populated after implementation._
