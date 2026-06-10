---
status: backlogged
story_ids: [77, 78, 79, 80]
milestone: Multilingual Meeting Support
---

# Spec: Multilingual Transcription (Mixed-Language Meetings)

## Overview

### Problem Statement

Nimble's sales team regularly records meetings that mix English and Thai — sometimes alternating between the two within a single call as participants switch languages by topic or by who is speaking. The Meeting Transcriber currently assumes **one language per meeting**: the uploader picks a single language (or "auto-detect"), and WhisperX detects one language from the opening of the recording and transcribes the entire file as that language. When a meeting is genuinely bilingual, every passage in the non-dominant language is transcribed incorrectly — Whisper renders it as garbled phonetics or hallucinated text in the wrong language. This makes the transcript unreliable for exactly the meetings that matter most to a bilingual sales team, and it is the top driver of the "transcription accuracy in mixed-language meetings" pain point already recorded in the project's known issues. This spec resolves Open Question #2 from [transcription-quality-improvements.md](transcription-quality-improvements.md), which deferred the decision on whether to support a multilingual transcription mode.

### Goals

- Produce an accurate transcript for meetings that contain more than one language, with each passage transcribed in the language actually spoken.
- Let a non-technical uploader declare which languages a meeting is expected to contain.
- Preserve the existing single-language experience unchanged — same flow, no added processing time — for the common monolingual case.
- Make detected language visible per segment so users can trust (and spot-check) the result.
- Recover partial value from downstream analysis (emotion) on the supported-language portions of a mixed meeting instead of discarding it wholesale.

### Scope

This spec covers:

- Selecting multiple expected languages at upload time (multi-select).
- Per-segment language detection and transcription for meetings with two or more expected languages.
- Per-language word-level alignment so timestamps and speaker assignment remain accurate across languages.
- Storing and displaying the detected language of each transcript segment.
- Extending emotion analysis to run per-segment on supported-language (English) segments rather than skipping the entire meeting.

Out of scope:

- **Translation** of any kind. The transcript preserves each segment in its original spoken language; there is no unified single-language rendering.
- **Mid-sentence code-switching accuracy.** When a speaker switches language within a single utterance, that utterance is transcribed as the dominant language of the chunk. Improving this is a known limitation, not a goal (see EC-5).
- **Cloud or external ASR / translation services.** The privacy constraint requires all processing to remain local.
- **A Thai (or other non-English) emotion-recognition model.** No validated local model exists; Thai segments are marked unavailable. Sourcing one is a future consideration.
- **Custom vocabulary and post-processing**, covered by [vocabulary-and-post-processing.md](vocabulary-and-post-processing.md).
- **Thai alignment model setup**, already delivered in [transcription-quality-improvements.md](transcription-quality-improvements.md) (US-3).

## User Stories

### Meeting Uploader (Sales User)

- As an **uploader**, I can select more than one expected language for a meeting, so that a mixed English/Thai recording is transcribed in the correct language passage by passage instead of forcing the whole file into one language.
- As an **uploader**, I can leave the language selection as a single language (or auto-detect) and have the meeting processed exactly as it is today, so that monolingual meetings gain no extra complexity or processing time.
- As an **uploader**, I can see which language each segment was detected as in the transcript view, so that I can quickly spot and judge any mis-detected passages.
- As an **uploader** of a mixed meeting who enabled emotion analysis, I still get emotion results for the English portions of the conversation, so that turning on a bilingual meeting does not silently discard all emotional insight.

## Business Rules

### Language Selection

| # | Rule | Rationale |
|---|------|-----------|
| BR-1 | A meeting carries a set of expected languages. Selecting zero languages means "auto-detect a single language" (current default behavior). | Preserves today's experience as the default and frames multilingual as an explicit opt-in. |
| BR-2 | When the expected-language set contains zero or one language, the meeting is processed through the existing single-language path with no per-segment detection. | The per-segment path adds processing cost; it must only apply when genuinely needed (EC-1, performance). |
| BR-3 | Per-segment (multilingual) processing is triggered only when two or more expected languages are selected. | This is the defining condition for the new behavior. |

### Per-Segment Detection & Transcription

| # | Rule | Rationale |
|---|------|-----------|
| BR-4 | In multilingual mode, language is detected per speech chunk produced by voice-activity detection, and each chunk is transcribed in its detected language. | This is the mechanism that lets the transcript follow turn- and sentence-level language switches. |
| BR-5 | Per-chunk language detection is constrained to the user-selected expected languages; the most probable language *within that set* is chosen for each chunk. | Constraining the candidate set improves both accuracy (fewer spurious languages) and speed versus open-set detection, and matches the uploader's stated intent. |
| BR-6 | If detection for a chunk is ambiguous or the chunk is too short to classify confidently, the chunk falls back to the meeting's dominant detected language. | Avoids erratic single-chunk mis-detections fragmenting the transcript. |
| BR-7 | A chunk containing mid-utterance code-switching is transcribed wholly as the dominant language of that chunk. | Whisper assigns one language per decode window; mid-utterance mixing is an accepted limitation (EC-5). |

### Alignment

| # | Rule | Rationale |
|---|------|-----------|
| BR-8 | Word-level alignment runs per language: segments are grouped by detected language and each group is aligned with that language's alignment model. | Alignment models are language-specific; grouping keeps timestamps accurate across the whole transcript. |
| BR-9 | Segments whose detected language has no available alignment model retain segment-level (chunk) timestamps. | Matches existing graceful-degradation behavior for unsupported alignment languages. |

### Downstream Analysis

| # | Rule | Rationale |
|---|------|-----------|
| BR-10 | Emotion analysis is evaluated per segment: English segments are analyzed; segments in a language unsupported by the emotion model are marked unavailable. The whole meeting is no longer skipped solely because it contains non-English speech. | The emotion model is validated only for English; per-segment gating recovers value from the English portion of a mixed meeting without producing untrustworthy labels for other languages. |
| BR-11 | Prosody and interaction analysis remain language-agnostic and are unaffected by per-segment language. | These stages do not depend on language; only emotion (SER) is language-gated. |

### Presentation

| # | Rule | Rationale |
|---|------|-----------|
| BR-12 | Each transcript segment displays a badge indicating its detected language. | Gives users a fast way to trust the result and spot mis-detections. |

## Edge Cases

| # | Scenario | Expected Behavior |
|---|----------|--------------------|
| EC-1 | Two+ languages selected, but the audio turns out to be entirely one of them | Every chunk is detected as that one language; the transcript is effectively monolingual. The meeting still incurs per-chunk detection cost (acceptable; the uploader opted in). |
| EC-2 | Audio contains a language the uploader did **not** select | Constrained detection (BR-5) forces those chunks into the nearest selected language, producing mis-transcription for that passage. Documented limitation; the remedy is for the uploader to select the correct languages and retry. |
| EC-3 | A chunk's detected language has no alignment model configured | That chunk keeps segment-level timestamps (BR-9); transcription text is unaffected. |
| EC-4 | A chunk is too short or ambiguous to classify | Falls back to the meeting's dominant language (BR-6) rather than guessing per chunk. |
| EC-5 | A single utterance switches language mid-sentence ("เราจะ deploy ตอน Friday") | Transcribed wholly as the dominant language of the chunk (BR-7). Known limitation; not corrected by this spec. |
| EC-6 | Mixed meeting with emotion analysis enabled | Emotion runs on English segments; non-English segments are marked unavailable (BR-10). The meeting is not skipped. |
| EC-7 | Only one language selected | Single-language path runs unchanged (BR-2); no per-segment detection, no added time, identical to current behavior. |
| EC-8 | A meeting transcribed before this feature is viewed or retried | Existing segments default to the meeting's primary language for the badge; retrying re-processes under the new model and selected languages. |

## Open Questions

| # | Question | Owner | Status |
|---|----------|-------|--------|
| OQ-1 | Should there be a configurable global default expected-language set (e.g., English + Thai) so the common bilingual case is preselected and uploaders save clicks? | Product | Resolved — no. The multi-select has no pre-selection; uploaders choose languages explicitly each time. |
| OQ-2 | What is the acceptable processing-time increase for multilingual meetings relative to single-language? | Product / Engineering | Resolved — any increase is acceptable provided single-language meetings are unaffected, which BR-2 guarantees. |
| OQ-3 | Should per-chunk detection be strictly constrained to the selected set (BR-5), or allow open-set detection with the selected set only as a prior? Constrained is the current decision for accuracy and speed. | Engineering | Resolved — constrained to the selected set (BR-5). |
| OQ-4 | Is there a viable local Thai speech-emotion-recognition model worth evaluating so Thai segments can also receive emotion analysis? | Engineering | Open — out of scope for this spec; tracked as a future consideration. |
| OQ-5 | Should the transcript export/copy formats include the per-segment language, or is the badge UI-only? | Product / Design | Resolved — badge is UI-only; export/copy formats are unchanged. |
