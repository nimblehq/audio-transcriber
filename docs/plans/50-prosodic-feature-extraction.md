# Plan: Prosodic Feature Extraction

**Story**: #50
**Spec**: docs/specs/audio-emotional-intelligence.md
**Branch**: feature/50-prosodic-feature-extraction
**Date**: 2026-04-28
**Mode**: Standard — signal processing is hard to TDD-drive without real audio fixtures; tests use synthetic numpy waveforms (sine waves, silence) to validate the math deterministically.

## Technical Decisions

### TD-1: Prosody tool — `praat-parselmouth`
- **Context**: Story is for sales meeting analysis where pitch accuracy directly impacts hesitation/confidence detection. Initial proposal of `torchaudio.detect_pitch_frequency` (NCCF autocorrelation) is too coarse — it misses voicing decisions, octave errors, and unvoiced frame masking.
- **Decision**: Use `praat-parselmouth` (Praat via a Python wrapper). Praat's pitch tracker is the de-facto standard in academic speech prosody. Also gives proper intensity (dB SPL) and handles voicing decisions natively.
- **Alternatives considered**:
  - `torchaudio.functional.detect_pitch_frequency` — zero new deps but inadequate accuracy for sales-meeting prosody.
  - `librosa.pyin` — high-quality PYIN pitch but `librosa` pulls a heavier transitive tree (~250MB) and we'd still want intensity from elsewhere.
  - OpenSMILE — most comprehensive feature set but heavyweight install and a config-file workflow that doesn't match the rest of the codebase.

### TD-2: Per-stage status in `AudioAnalysis`
- **Context**: Story #49 introduced one rolled-up `status` field on `AudioAnalysis`. Prosody is language-agnostic (BR-2.1) while SER is English-only. With both stages present, a single status can't represent "emotions skipped, prosody completed".
- **Decision**: Add `emotion_status`/`emotion_reason` and `prosody_status`/`prosody_reason` per-stage fields. Keep the top-level `status` as a roll-up: `COMPLETED` if any stage produced output, `FAILED` only if every applicable stage failed, `UNAVAILABLE` only if every stage was skipped (rare).
- **Alternatives considered**: Two separate output files (`emotion_analysis.json`, `prosody_analysis.json`). Simpler per stage but breaks the "audio analysis is one feature" mental model and complicates retry.

### TD-3: Volume normalization across the meeting
- **Context**: AC requires `volume_mean` to be normalized 0–1 within the meeting (BR-2.2). Per-segment dB intensity is comparable across segments but not bounded.
- **Decision**: Compute raw RMS energy per segment, then divide by the meeting's max RMS in a final pass. `volume_variance` is computed on the same normalized scale so it stays comparable. Pitch is left in Hz (already comparable across speakers, no normalization needed).
- **Alternatives considered**: Per-speaker baseline calibration (story acknowledges this is an open question). Deferred — meeting-level normalization satisfies the AC and avoids the need for speaker-specific reference passages.

### TD-4: Speaking rate from text + duration
- **Context**: Speaking rate could come from word-level WhisperX timestamps, but those only exist when alignment ran (`detected_language` is in the supported set). For other languages, we still need a value.
- **Decision**: Compute WPM as `len(text.split()) / duration_seconds * 60`. Works regardless of alignment. Slight drift from "true" syllable rate but consistent across the meeting.
- **Alternatives considered**: Word-level timestamps from `result["segments"][i]["words"]` when present. More precise but inconsistent across languages — Thai (one of the project's first-class languages) often loses alignment.

### TD-5: Non-speech detection — RMS floor + voicing ratio
- **Context**: AC5/BR-2.3 require non-speech segments (silence, music, hold tones) to be excluded.
- **Decision**: A segment is non-speech when (a) its raw RMS is below `1e-3` AND (b) Praat's pitch tracker yielded zero voiced frames. This catches silence and hold tones reliably; pure music is rare in sales meetings and would still get a `prosody_unavailable` flag if extraction throws.
- **Alternatives considered**: Run a dedicated VAD (Silero, webrtcvad). Adds another model dependency for marginal benefit at this scope.

## Files to Create or Modify

- `requirements.txt` — add `praat-parselmouth>=0.4.7`.
- `backend/schemas.py` — add `ProsodyAnnotation`, `ProsodyUnavailable`. Refactor `AudioAnalysis` with per-stage status fields. Add `JobStage.PROSODY_EXTRACTION`.
- `backend/services/prosody_analyzer.py` *(new)* — `analyze_segments(audio_array, segments) -> tuple[list[ProsodyAnnotation], list[ProsodyUnavailable]]`. Helpers for RMS, pitch (via parselmouth), pause ratio, WPM, non-speech detection. Final pass normalizes volume across the meeting.
- `backend/services/transcriber.py` — refactor `_run_audio_analysis` to run prosody **always** (when opted in) and SER only for English. Both run best-effort, surfaced via per-stage status.
- `tests/unit/test_prosody_analyzer.py` *(new)* — synthetic-signal tests for each feature, normalization across segments, non-speech detection, per-segment failure tolerance.
- `tests/unit/test_schemas.py` — schema validation for new prosody fields.
- `tests/unit/test_transcriber.py` — update `TestRunAudioAnalysis` for the new pipeline shape.

## Approach per AC

### AC 1 / AC 2: Per-segment prosody annotations with all required fields
Analyzer returns `ProsodyAnnotation` with `segment_id`, `speaker`, `start`, `end`, `volume_mean` (0–1), `volume_variance`, `pitch_mean` (Hz), `pitch_variance`, `speaking_rate` (WPM), `pause_ratio`.

### AC 3: `segment_id` linkage
Reuses `TranscriptSegment.id`.

### AC 4: Cross-speaker comparability
Volume normalized across the meeting (TD-3). Pitch in raw Hz. Speaking rate in absolute WPM. Per-speaker baseline calibration deferred.

### AC 5: Non-speech segments excluded with metadata note
Non-speech detection per TD-5. Recorded in `prosody_unavailable` with `reason="non_speech"`.

### AC 6: Per-segment failure tolerance
Try/except per segment. Failures recorded in `prosody_unavailable` with `reason="prosody_unavailable"`. The stage continues.

### AC 7: Skipped when audio analysis opted out
No new code path. Existing `if metadata.audio_analysis_enabled:` gate covers it.

### AC 8: Persisted alongside emotion annotations
Same `audio_analysis.json` file; new `prosody` and `prosody_unavailable` arrays under the existing `AudioAnalysis` envelope.

### BR-2.1: Language-agnostic
Prosody runs regardless of detected language. Only SER stays English-gated.

## Commit Sequence

1. `[#50] Persist implementation plan`
2. `[#50] Add praat-parselmouth dependency`
3. `[#50] Add prosody schemas and per-stage audio analysis status`
4. `[#50] Add prosody analyzer service`
5. `[#50] Wire prosody extraction into audio analysis pipeline`
6. `[#50] Add prosody analyzer and pipeline tests`

## Risks and Trade-offs

- **No per-speaker baseline calibration.** Meeting-level normalization satisfies the AC but won't account for individual speakers who naturally speak louder/faster. Tracked as future work.
- **Speaking rate from text length.** Approximate vs. true syllable rate but consistent and language-agnostic.
- **Praat is single-threaded.** Slower than a tensor-based extractor on long meetings. Negligible vs. SER cost.
- **Synthetic test signals only.** Unit tests use sine waves and silence; real-audio behavior validated manually.

## Deviations from Spec

- Spec lists OpenSMILE/Praat/librosa/PyAudioAnalysis as candidates; we use `praat-parselmouth` (TD-1).
- Spec includes jitter/shimmer in voice quality features; story AC does not require them, so they're omitted from this slice.
- Spec defines `EnhancedSegment` extending the transcript; we keep transcript untouched and add prosody to the existing sibling `audio_analysis.json` file (continuation of Story #49's storage decision).

## Deviations from Plan

- **Added `too_short` unavailable marker.** QA flagged that sub-`MIN_SEGMENT_SECONDS` segments were silently skipped, violating the truth that every segment must have either prosody data or an explicit unavailable marker. The plan's "skipped silently" behavior was changed to emit a `ProsodyUnavailable` with `reason="too_short"`. Driven by the QA verdict.
