# Plan: Interaction Pattern Detection

**Story**: #51
**Spec**: docs/specs/audio-emotional-intelligence.md
**Branch**: feature/51-interaction-pattern-detection
**Date**: 2026-04-29
**Mode**: Standard — pure-logic analysis on segment timestamps; tests use synthetic segment fixtures, no audio fixtures needed.

## Technical Decisions

### TD-1: Use raw PyAnnote `diarize_segments` for true overlap detection
- **Context**: WhisperX's `assign_word_speakers` collapses output into non-overlapping per-speaker segments; true overlap data only lives in PyAnnote's raw output. BR-3.1 requires detecting "Speaker B starts before Speaker A finishes their turn" — a real overlap.
- **Decision**: In the transcriber, normalize the diarization DataFrame into a plain `list[tuple[float, float, str]]` (start, end, speaker) and pass it to the interaction analyzer alongside transcript segments. Without diarization (no `HF_TOKEN`), the interaction stage marks `UNAVAILABLE`.
- **Alternatives considered**: Detect interruption from adjacent transcript segments where gap < 0. Misses most real overlaps because the transcript stream is serialized.

### TD-2: Back-channel heuristic — duration + lexical filter
- **Context**: Story leaves the heuristic to engineering and warns it must not inflate the interruption count.
- **Decision**: A diarization turn is a back-channel when its duration ≤ 1.5s AND its corresponding transcript text matches a curated set of acknowledgement tokens (`uh-huh`, `mm-hmm`, `yeah`, `right`, `ok`, `sure`, `i see`, etc.) — either as the whole utterance or, for ≤3-word utterances, as one of the words. Transcript text is looked up from the transcript segment overlapping the turn's midpoint.
- **Alternatives considered**: Pure duration filter (false positives on short content like "Tuesday"); lexical-only (false positives on long agreement statements).

### TD-3: Pause thresholds
- **Context**: Story leaves the threshold to engineering; AC requires capturing duration before each turn.
- **Decision**: `HESITATION_MIN_SECONDS = 0.7`, `LONG_PAUSE_MIN_SECONDS = 3.0`. A `hesitation` event fires when `0.7 ≤ gap < 3.0`; a `long_pause` event fires when `gap ≥ 3.0`. `hesitation_before` on each segment always carries the gap from the prior speaker's end (clamped ≥ 0), independent of whether a hesitation event was emitted.
- **Alternatives considered**: Speaker-relative thresholds (per-speaker baseline). Out of scope; deferred.

### TD-4: Segment annotations stored as a sibling list, not on transcript
- **Context**: Spec's `EnhancedSegment` shows the booleans/hesitation_before as transcript fields. Story #49/#50 decided to keep transcript schema untouched and put audio analysis in a sibling file.
- **Decision**: Add `segment_interactions: list[SegmentInteraction]` inside `AudioAnalysis`, keyed by `segment_id`, carrying `preceded_by_interruption`, `followed_by_interruption`, `hesitation_before`. Frontend joins by segment ID when needed.

### TD-5: Dominance flag on `AudioAnalysis`
- **Context**: AC says "records a `dominant_speaker_limitation` flag in metadata". The audio_analysis.json envelope is the audio analysis metadata.
- **Decision**: `dominant_speaker_limitation: bool = False` lives on `AudioAnalysis`. Computed from total speaking duration per speaker on the transcript segments — > 80% triggers the flag. Stage still completes successfully (BR-3.4).

## Files to Create or Modify

- `backend/schemas.py` — add `InteractionEventType` enum, `InteractionEvent`, `SegmentInteraction` models. Extend `AudioAnalysis` with interaction fields and `dominant_speaker_limitation`. Add `JobStage.INTERACTION_ANALYSIS`.
- `backend/services/interaction_analyzer.py` *(new)* — `analyze(transcript_segments, diarize_turns) -> InteractionAnalysisResult`. Helpers for back-channel detection, overlap classification, pause/hesitation events, segment annotation builder, dominance check.
- `backend/services/transcriber.py` — capture `diarize_segments` as a normalized list, add `_run_interaction_analysis`, wire into `_run_audio_analysis`, update roll-up to include the new stage.
- `tests/unit/test_interaction_analyzer.py` *(new)* — synthetic-segment tests for back-channel filtering, interruption vs overlap, hesitation/long-pause events, segment annotations, dominance flag.
- `tests/unit/test_schemas.py` — schema validation for new interaction fields.
- `tests/unit/test_transcriber.py` — extend `TestRunAudioAnalysis` for the three-stage pipeline.

## Approach per AC

### AC 1: Interaction stage produces events when audio analysis is opted in
`_run_interaction_analysis` invoked when `audio_analysis_enabled` and diarize_turns are present. Produces an `interactions` list on `AudioAnalysis`.

### AC 2: Each event has all required fields
`InteractionEvent { event_type, timestamp, speaker_a, speaker_b, duration, context }`. Context taken from transcript segment overlapping the event timestamp (truncated to ~120 chars).

### AC 3: Interruptions ≠ back-channels
Back-channel heuristic (TD-2) classifies the overlapping turn as an `overlap` event rather than `interruption`. Non-back-channel overlaps emit `interruption`.

### AC 4: Hesitation before each turn captured per segment
For every segment, `hesitation_before` = max(0, segment.start − prior_turn.end). Stored in `SegmentInteraction`. A `hesitation` event is emitted when the gap falls in the threshold band.

### AC 5: Single-speaker dominance still completes
Compute speaker shares from transcript segment durations; if `max_share > 0.8`, set `dominant_speaker_limitation = True`. Stage continues.

### AC 6: Per-segment interruption booleans
For each `interruption` event, mark `preceded_by_interruption = True` on the segment containing the interrupter's start, and `followed_by_interruption = True` on the segment containing the prior turn's overlap point. Builder iterates events once.

### AC 7: Skipped when opted out
No new code path — existing `if metadata.audio_analysis_enabled:` gate covers it.

### AC 8: No new model inference
Pure timestamp arithmetic + lexical lookup; no new dependencies.

## Commit Sequence

1. `[#51] Persist implementation plan`
2. `[#51] Add interaction event schemas and audio analysis fields`
3. `[#51] Add interaction analyzer service`
4. `[#51] Wire interaction analysis into transcription pipeline`
5. `[#51] Add interaction analyzer and pipeline tests`

## Risks and Trade-offs

- **Back-channel lexical list is English-biased.** Multilingual back-channel detection (Thai, French) is out of scope for this slice — non-English interjections may be misclassified as interruptions. Documented as a known limitation.
- **Context strings are truncated and may straddle turn boundaries.** Acceptable for AC; UI can re-derive richer context from the transcript using the timestamp.
- **No raw PyAnnote → no interactions.** Without `HF_TOKEN`, interaction stage marks `UNAVAILABLE`. Same convention as prosody/emotion when prerequisites are missing.
- **Threshold values are engineering judgments.** 0.7s hesitation / 3.0s long_pause / 1.5s back-channel-max / 0.8 dominance ratio — all tunable via constants.

## Deviations from Spec

- Spec's `EnhancedSegment` extends transcript with the interaction booleans; we keep transcript untouched and add `segment_interactions` to `AudioAnalysis` (continuation of storage decision from #49/#50).
- Spec lists "back-channel" as a detection category; we use it only as a *filter* on overlaps since the AC's `event_type` set is `{interruption, overlap, long_pause, hesitation}`.

## Deviations from Plan

_Populated after implementation._
