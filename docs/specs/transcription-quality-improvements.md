---
status: implemented
story_ids: [10]
last_verified: 2026-03-14
---

# Transcription & Diarization Quality Improvements

## Overview

### Problem Statement

The Meeting Transcriber is in daily use by Nimble's sales team, but transcription and diarization quality is a recurring pain point:

- **Transcription errors:** Proper nouns, technical terms, and brand names are frequently misrecognized.
- **Speaker merging:** Pyannote diarization sometimes collapses distinct speakers into one, even in small meetings (3-4 people).
- **Thai language gaps:** Thai alignment is skipped entirely (no wav2vec2 model configured), reducing timestamp precision and downstream diarization accuracy for Thai and mixed-language recordings.
- **Audio quality challenges:** Recordings come from Plaud devices or phone calls in large meeting rooms where the mic is often far from some speakers, introducing noise and low signal levels.

### Goals

1. Reduce word-level transcription errors, especially for proper nouns and technical terms.
2. Reduce speaker merging errors in diarization.
3. Add Thai language alignment support.
4. Improve robustness to poor audio conditions (far-field mic, room noise).

### Scope

Backend transcription pipeline changes only. No changes to the core UI layout or navigation. Minor upload form additions for new configuration options.

### Out of Scope

- Switching away from WhisperX or Pyannote
- Real-time transcription
- Cloud deployment or GPU infrastructure
- Performance optimization (speed)

## User Stories

### US-1: Audio Preprocessing

As a user uploading a meeting recorded in a large room, I want the system to automatically clean up the audio before transcription so that distant speakers and background noise don't degrade accuracy.

**Acceptance criteria:**
- Audio undergoes preprocessing (high-pass filter, noise reduction, loudness normalization) before transcription
- Preprocessing is enabled by default but can be disabled per upload
- Preprocessing does not degrade quality for clean, close-mic recordings

### US-2: Vocabulary Hints (Initial Prompt)

As a user, I want to provide context about the meeting (attendee names, company names, technical terms) so that the transcriber recognizes these words correctly.

**Acceptance criteria:**
- Upload form includes an optional "Context / vocabulary hints" text area
- Global default hints can be configured (e.g., company name, common terms)
- Hints are passed to WhisperX as `initial_prompt`
- UI indicates the ~150 word practical limit

### US-3: Thai Language Alignment

As a user transcribing Thai or mixed English/Thai meetings, I want the system to perform word-level alignment for Thai audio so that timestamps and speaker assignments are as accurate as for English.

**Acceptance criteria:**
- Thai (`th`) is added to supported alignment languages
- Uses `airesearch/wav2vec2-large-xlsr-53-th` alignment model
- Thai alignment model is downloaded on first use (same as other alignment models)

### US-4: Improved Diarization Controls

As a user, I want to provide a speaker count range (min/max) instead of an exact number so that the diarization algorithm has better constraints without requiring me to know the exact count.

**Acceptance criteria:**
- Upload form supports min speakers and max speakers fields (in addition to existing exact count)
- When exact count is provided, min/max are ignored
- When only min is provided, diarization preserves at least that many speakers
- Default behavior (no hints) remains unchanged

### US-5: Diarization Sensitivity Tuning

As an administrator, I want to configure the diarization clustering threshold so that the system can be tuned to favor splitting over merging speakers.

**Acceptance criteria:**
- `DIARIZATION_THRESHOLD` env var controls clustering sensitivity
- Default value preserves current behavior
- Lower values reduce speaker merging (at the cost of potential over-splitting)
- Requires replacing WhisperX's diarization wrapper with direct pyannote Pipeline usage

## Business Rules

| ID | Rule | Rationale |
|----|------|-----------|
| BR-1 | `initial_prompt` is truncated to 224 tokens (Whisper's internal limit). UI warns at ~150 words. | Whisper silently drops tokens beyond 224, which could mislead users. |
| BR-2 | `min_speakers`/`max_speakers` are mutually exclusive with `num_speakers`. If exact count is set, range is ignored. | Pyannote does not accept both simultaneously. |
| BR-3 | Audio preprocessing uses conservative noise reduction (`prop_decrease=0.75`). | Whisper was trained on noisy data. Aggressive noise removal can strip speech harmonics and hurt accuracy. |
| BR-4 | Global vocabulary hints are prepended to per-meeting hints. Per-meeting hints take priority (placed last in prompt, where attention weight is highest). | Whisper's decoder assigns higher attention to tokens at the end of the initial prompt. |
| BR-5 | Thai alignment model is loaded on-demand, not at startup. | Avoids downloading/loading models for languages not in use. Consistent with existing alignment model behavior. |

## Data Requirements

### Schema Changes (MeetingMetadata)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `initial_prompt` | `str \| None` | `None` | Vocabulary hints / context for Whisper decoder |
| `min_speakers` | `int \| None` | `None` | Minimum expected speakers (diarization hint) |
| `max_speakers` | `int \| None` | `None` | Maximum expected speakers (diarization hint) |
| `preprocess_audio` | `bool` | `True` | Whether to apply audio preprocessing |

### Configuration (env vars)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DIARIZATION_THRESHOLD` | `float` | `0.715` (pyannote default) | Clustering threshold. Lower = more speakers preserved. |
| `DEFAULT_INITIAL_PROMPT` | `str` | `""` | Global default vocabulary hints prepended to per-meeting prompt. |

### Dependencies (new)

| Package | Version | Purpose |
|---------|---------|---------|
| `noisereduce` | `>=3.0.0` | Spectral gating noise reduction |
| `pyloudnorm` | `>=0.1.1` | ITU-R BS.1770 loudness normalization |

## Edge Cases

| Case | Expected Behavior |
|------|-------------------|
| `initial_prompt` exceeds 224 tokens | Whisper silently truncates from the start. UI shows a warning when input is long. |
| Language auto-detect returns a language not in alignment list | Alignment is skipped gracefully (current behavior). Transcript uses segment-level timestamps. |
| Mixed-language meeting (English/Thai) | Auto-detect picks dominant language. Alignment uses that language's model. Words in the secondary language may have less precise timestamps. |
| `min_speakers` > actual speakers | Diarization may split one speaker into multiple. Acceptable tradeoff vs. merging. |
| Audio is already clean (close-mic) | Preprocessing with conservative settings should not degrade quality. User can disable per upload if needed. |
| `DIARIZATION_THRESHOLD` set too low | Over-splitting (one speaker appears as multiple). Documented in config with recommended range (0.4-0.8). |
| Thai alignment model not yet downloaded | Downloaded automatically on first Thai transcription. May add ~1-2 min to first run. |

## Open Questions

| # | Question | Impact |
|---|----------|--------|
| 1 | Should preprocessing be applied before diarization only, before transcription only, or both? Using preprocessed audio for both is simpler but Whisper may handle raw audio better for transcription while diarization benefits more from clean audio. | Architecture: may need two audio paths |
| 2 | For mixed English/Thai meetings, should users be able to specify "multilingual" as a language option to trigger alignment with multiple models? | Scope: significant complexity increase |
| 3 | Should `DIARIZATION_THRESHOLD` be exposed per-meeting in the upload form, or kept as admin-only config? | UX: per-meeting adds complexity for non-technical users |
| 4 | Is the `pyannote/speaker-diarization-community-1` model worth evaluating as an alternative to 3.1? It reportedly improves speaker counting but has different licensing. | Licensing and accuracy evaluation needed |

## Implementation Notes

**Suggested implementation order (incremental, each deliverable independently):**

1. **Thai alignment** — Smallest change (~10 lines), immediate value for Thai meetings.
2. **Vocabulary hints** — Schema + form field + 3 lines in transcriber. Quick win for proper noun accuracy.
3. **Speaker count range** — Schema + form fields + pass-through to pyannote. Low effort.
4. **Audio preprocessing** — New dependencies, new pipeline stage. Medium effort, high impact.
5. **Diarization threshold tuning** — Requires replacing WhisperX wrapper with direct pyannote usage. Largest refactor.
