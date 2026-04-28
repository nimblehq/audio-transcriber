# Plan: Audio Analysis Opt-in and Speech Emotion Recognition

**Story**: #49
**Spec**: docs/specs/audio-emotional-intelligence.md
**Branch**: feature/49-audio-analysis-opt-in
**Date**: 2026-04-28
**Mode**: Standard — heavy ML model integration is hard to TDD-drive without real audio fixtures; tests cover schema, opt-in persistence, language gating, and analyzer interface with mocks.

## Technical Decisions

### TD-1: SER model — `ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition`
- **Context**: Need a Speech Emotion Recognition model that maps cleanly to the spec's 6 emotion categories and integrates with the existing torch/whisperx stack.
- **Decision**: Use `ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition` via HF `transformers.pipeline("audio-classification", ...)`. The 8 raw labels (angry, calm, disgust, fearful, happy, neutral, sad, surprised) are mapped to the spec's 6 categories.
- **Alternatives considered**: Emotion2Vec (multilingual but requires funasr — heavy dep tree, ModelScope-hosted models, Linux-classified). Audeering valence/arousal model (dimensional, not categorical — would require deriving categories heuristically).

### TD-2: Storage — sibling file `audio_analysis.json`
- **Context**: Spec calls out storage layout as an engineering decision.
- **Decision**: Store annotations in a sibling file rather than extending `transcript.json`. Keeps transcript schema unchanged (full backward compat per AC9). Allows independent regeneration.
- **Alternatives considered**: Extending each transcript segment with an `emotion` field — couples the two schemas and complicates retry.

### TD-3: Pipeline placement — inline in transcription thread, after diarization, best-effort
- **Context**: Spec mentions parallel processing as an option.
- **Decision**: Run inline in the same thread, after diarization completes. Wrap in try/except so failures set `audio_analysis_status="failed"` without failing the meeting (AC8, BR-1.4).
- **Alternatives considered**: Separate background thread/queue — adds complexity for marginal gain at current scale.

### TD-4: Language gating — English-only for Phase 1
- **Context**: SER models suitable for English-only; multilingual models require funasr (heavy dep). Project supports many languages including Thai.
- **Decision**: Run SER only when detected language is English. For other languages, set `audio_analysis_status="unavailable"`. UI surfaces "currently English only" note on the toggle.
- **Alternatives considered**: Run model on all languages and accept degraded accuracy (misleading users), or pull funasr (option rejected for dep cost).

### TD-5: Confidence flag stored on write
- **Context**: BR-1.2 requires confidence < 0.5 to be flagged.
- **Decision**: Persist `low_confidence: bool` directly in the annotation alongside `confidence`. Avoids downstream re-derivation.

## Files to Create or Modify

- `backend/schemas.py` — add `EmotionCategory`, `AudioAnalysisStatus` enums; `EmotionAnnotation`, `AudioAnalysis` models; extend `MeetingMetadata`; extend `JobStage`.
- `backend/services/emotion_analyzer.py` *(new)* — `analyze_segments(audio_path, segments) -> AudioAnalysis`. Lazy-loads HF pipeline, classifies each segment, maps labels.
- `backend/services/transcriber.py` — after diarization, gate by language and call analyzer; persist `audio_analysis.json`; update `audio_analysis_status` and job stage.
- `backend/routers/meetings.py` — accept `audio_analysis_enabled` form field on upload.
- `frontend/js/components/upload.js` — opt-in checkbox with benefits + time-cost + English-only note.
- `frontend/js/api.js` — pass `audioAnalysisEnabled` flag in form data.
- `frontend/css/styles.css` — minor styling for the disclosure block.
- `tests/unit/test_schemas.py` — schema validation for new fields.
- `tests/unit/test_emotion_analyzer.py` *(new)* — label mapping, low-confidence flag, mocked HF pipeline.
- `tests/integration/test_meetings.py` — assert opt-in persists, defaults to false.

## Approach per AC

### AC 1: Toggle defaulted to off on upload form
Checkbox in `upload.js`, unchecked by default. Form field sent only when checked.

### AC 2: Benefits + cost copy
Disclosure block under the toggle listing per-speaker emotion, prosody, interaction dynamics, word-tone mismatches, plus the "+8 to 17 minutes (~+50%)" cost. Includes English-only note.

### AC 3 / AC 4: Opt-in persists in metadata
Router reads `audio_analysis_enabled` form field, parses to bool, stores on `MeetingMetadata`. Default false.

### AC 5: SER stage runs when enabled
`_run_transcription` checks `metadata.audio_analysis_enabled`. If true and detected language is English, run analyzer. Job stage set to `emotion_analysis` while running.

### AC 6: Annotation fields
`EmotionAnnotation { segment_id, speaker, start, end, primary_emotion, confidence, emotion_scores, low_confidence }`. Saved into `audio_analysis.json`.

### AC 7: Low-confidence flag
`low_confidence = confidence < 0.5` written to each annotation.

### AC 8: Failures don't fail meeting
Try/except around the analyzer call. On failure: log, set `audio_analysis_status="failed"`, continue to mark meeting READY.

### AC 9: Backward compat
Default off; analyzer never invoked. No transcript schema change. No new files written for opted-out meetings.

## Commit Sequence

1. `[#49] Persist implementation plan`
2. `[#49] Add audio analysis schemas and metadata fields`
3. `[#49] Add SER emotion analyzer service`
4. `[#49] Wire emotion analysis into transcription pipeline`
5. `[#49] Accept audio_analysis_enabled on upload endpoint`
6. `[#49] Add audio analysis opt-in toggle to upload form`
7. `[#49] Add tests for opt-in persistence and analyzer`

## Risks and Trade-offs

- **Model download size** (~1GB). First analysis is slow — surfaced via `emotion_analysis` job stage.
- **Label mapping is fuzzy.** 8→6 mapping is approximate. Acknowledged in the spec.
- **English-only Phase 1.** Story #49 ships an end-to-end vertical slice for English. Multilingual support tracked as future work.
- **No real audio fixture in tests.** Analyzer tests mock the HF pipeline; full SER behavior validated manually.

## Deviations from Spec

- Spec recommends "always on" for Phase 1; story explicitly overrides this with opt-in. Plan follows the story.
- Spec defines `EnhancedSegment` extending the transcript; we keep transcript untouched and store annotations in a sibling file (TD-2). The spec lists storage layout as an engineering decision.
- Spec lists Emotion2Vec/SpeechBrain as candidates; we chose HF wav2vec2 (TD-1) and gate by language (TD-4) to avoid funasr dependency cost. Multilingual SER is deferred.

## Deviations from Plan

- **SER model changed from `ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition` to `firdhokk/speech-emotion-recognition-with-openai-whisper-large-v3`.** During QA the ehcalabres checkpoint was found to load with random classifier weights under standard `Wav2Vec2ForSequenceClassification` (the saved 2-layer head — `classifier.dense`/`classifier.output` — does not match the standard 1-layer head). Predictions were effectively random. Switched to firdhokk's whisper-large-v3-based model which loads cleanly and produces 7 emotion labels. The label map was updated accordingly. Trade-off: no model label maps to `CONFIDENT`, so that spec category will not appear in current outputs. Documented as a known limitation in the analyzer comments.
- **HF `transformers.pipeline` replaced with direct `AutoFeatureExtractor` + `AutoModelForAudioClassification` calls.** The pipeline's preprocess step calls `import torchcodec` on every invocation, even when input is a pre-decoded numpy array. If the local torchcodec install is broken (a common state on macOS when torch and torchcodec ABIs drift apart), every classification raises and yields zero annotations. Replaced with a `_DirectClassifier` wrapper that bypasses the pipeline entirely and produces the same output shape. The torchcodec env hygiene is tracked separately as chore #56.
