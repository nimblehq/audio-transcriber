# Vocabulary & Post-Processing Quality Improvements

## Overview

### Problem Statement

The Meeting Transcriber uses WhisperX for transcription, which has no native support for custom vocabulary or "hot words." As a result, proper nouns (people's names, company names), acronyms, and domain-specific terms are frequently misrecognized. Competing products like Plaud achieve better proper noun accuracy through persistent custom vocabularies with phonetic matching and LLM-based post-processing — both applied *after* the core ASR step.

The existing spec ([transcription-quality-improvements.md](transcription-quality-improvements.md)) addresses this partially through `initial_prompt` vocabulary hints (US-2), which primes Whisper's decoder. However, `initial_prompt` is limited to 224 tokens and only influences the decoder's probability distribution — it does not guarantee correct output. A post-processing layer is needed to catch and correct remaining errors.

### Goals

1. Achieve ≥90% correct transcription of terms in the user's custom vocabulary.
2. Provide a persistent, reusable vocabulary system (not just per-meeting hints).
3. Add an optional LLM-based correction pass for transcripts.
4. Improve Thai transcription output quality through language-specific post-processing.
5. Names and acronyms that users add to their vocabulary should "just work" across all future transcriptions.

### Scope

- Persistent custom vocabulary (file-based + UI management)
- Phonetic matching post-processor for English and Thai
- Optional local LLM correction pass (post-transcription, user-triggered)
- Thai text normalization via PyThaiNLP
- Integration with existing `initial_prompt` feature from the parent spec

### Out of Scope

- Cloud-based ASR or correction APIs (privacy constraint)
- Pre-built industry glossaries (future consideration)
- Real-time correction during transcription
- WhisperX model fine-tuning
- Changing the core ASR engine

### Relationship to Parent Spec

This spec is a companion to [transcription-quality-improvements.md](transcription-quality-improvements.md). It builds on US-2 (Vocabulary Hints) by adding a persistent vocabulary layer and post-processing pipeline. The `initial_prompt` mechanism remains the first line of defense; this spec adds a second pass that catches what `initial_prompt` misses.

## User Stories

### US-1: Persistent Custom Vocabulary

As a user, I want to maintain a list of terms (names, acronyms, technical words) that the system should always recognize correctly, so that I don't have to re-enter vocabulary hints for every meeting.

**Acceptance criteria:**
- A vocabulary file (`config/vocabulary.txt`) stores terms, one per line
- The web app provides a UI page for viewing, adding, editing, and removing vocabulary terms
- Changes in the file are reflected in the UI and vice versa
- Vocabulary terms are automatically included in `initial_prompt` (within token limits) AND used for post-processing correction
- The vocabulary is global (applies to all meetings)

### US-2: Phonetic Post-Processing Correction

As a user, I want the system to automatically correct misrecognized words that sound similar to terms in my vocabulary, so that proper nouns and acronyms appear correctly in the transcript without manual editing.

**Acceptance criteria:**
- After transcription, a post-processing step compares transcript words against the custom vocabulary using phonetic similarity
- Phonetically similar words are auto-replaced with the vocabulary term
- Correction works for both English and Thai terms
- Corrections are applied silently (no user intervention required)
- Original uncorrected transcript is preserved (for debugging/rollback)

### US-3: Optional LLM Correction Pass

As a user, I want to optionally run an LLM-based correction on my transcript to fix contextual errors that phonetic matching can't catch, so that I get the highest possible quality when I need it.

**Acceptance criteria:**
- A "Polish transcript" action is available in the transcript viewer after transcription completes
- Correction runs via a local LLM (Ollama) — no data leaves the machine
- The LLM receives the transcript plus the custom vocabulary as context
- Corrections focus on proper nouns, acronyms, and obvious ASR errors — not style or rephrasing
- The user can see the corrected version and revert to the original
- The action is optional and user-triggered (not part of the automatic pipeline)
- Works within the hardware constraints of MacBook Air M2 / MacBook Pro M1

### US-4: Thai Text Normalization

As a user transcribing Thai meetings, I want the system to normalize Thai text output (word segmentation, formatting) so that the transcript is more readable and accurate.

**Acceptance criteria:**
- Thai transcription output is post-processed with PyThaiNLP for word segmentation normalization
- Thai numerals and common formatting issues are handled
- Normalization is automatic for Thai-language transcriptions
- Does not degrade English text in mixed-language segments

### US-5: Vocabulary Management UI

As a user, I want a page in the web app where I can manage my vocabulary list, so that I don't have to edit a text file manually.

**Acceptance criteria:**
- A "Vocabulary" page is accessible from the main navigation
- Users can add, edit, and delete terms
- Users can see the total term count
- Changes persist to the vocabulary file on disk
- The UI supports bulk import (paste multiple terms)

## Business Rules

| ID | Rule | Rationale |
|----|------|-----------|
| BR-1 | Vocabulary terms are injected into `initial_prompt` before per-meeting hints, ordered by frequency of past corrections. Total prompt respects the 224-token limit. | Maximizes the chance Whisper gets it right on the first pass. Most-corrected terms are most valuable to prime. |
| BR-2 | Phonetic matching uses a similarity threshold (configurable, default 0.85). Only matches above the threshold are auto-corrected. | Too low a threshold causes false positives (e.g., replacing common words). Too high misses valid corrections. |
| BR-3 | Phonetic matching preserves the original word's casing pattern when replacing (e.g., if the original is all-caps, the replacement is all-caps). | Maintains transcript formatting consistency. |
| BR-4 | The original uncorrected transcript is always preserved alongside the corrected version. | Enables debugging, rollback, and quality measurement. |
| BR-5 | LLM correction prompt explicitly instructs the model to only fix ASR errors and proper nouns — no style changes, no summarization, no content alteration. | Prevents the LLM from hallucinating or altering meaning. Research shows ~25% hallucination rate with unconstrained correction. |
| BR-6 | LLM correction is not available during active transcription — only after transcription completes. | Avoids resource contention on limited hardware (M1/M2 Macs). |
| BR-7 | Vocabulary terms are case-insensitive for matching but case-preserving for output. The vocabulary entry determines the canonical casing. | "nimble" in ASR output should become "Nimble" if that's how it's stored in vocabulary. |
| BR-8 | Per-meeting `initial_prompt` hints (from parent spec US-2) take priority over global vocabulary when token budget is limited. | Per-meeting context is more specific and valuable for that particular transcription. Consistent with BR-4 of the parent spec. |

## Data Requirements

### Vocabulary File Format

Plain text file at `config/vocabulary.txt`:
```
Nimble
Plaud
KBTG
IoT
FastAPI
WhisperX
PyAnnote
```

One term per line. Blank lines and lines starting with `#` are ignored.

### Schema Changes

No new fields on `MeetingMetadata`. The corrected transcript is stored as a separate file:

| File | Location | Description |
|------|----------|-------------|
| `vocabulary.txt` | `config/vocabulary.txt` | Global custom vocabulary, one term per line |
| `transcript_original.json` | `data/meetings/{id}/` | Pre-correction transcript (preserved for rollback) |
| `transcript.json` | `data/meetings/{id}/` | Post-correction transcript (what users see) |

### Configuration (env vars)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VOCABULARY_FILE` | `str` | `config/vocabulary.txt` | Path to vocabulary file |
| `PHONETIC_THRESHOLD` | `float` | `0.85` | Minimum phonetic similarity score for auto-correction (0.0–1.0) |
| `OLLAMA_MODEL` | `str` | `gemma3:4b` | Ollama model for LLM correction pass |
| `OLLAMA_BASE_URL` | `str` | `http://localhost:11434` | Ollama API endpoint |

### Dependencies (new)

| Package | Version | Purpose |
|---------|---------|---------|
| `jellyfish` | `>=1.0.0` | Phonetic algorithms (Metaphone, Soundex) for English |
| `pythainlp` | `>=5.0.0` | Thai NLP: word segmentation, phonetic romanization |
| `ollama` | `>=0.4.0` | Python client for local Ollama LLM |

## Edge Cases

| Case | Expected Behavior |
|------|-------------------|
| Vocabulary term matches a common English word (e.g., "Swift") | Phonetic matching should use context (surrounding words) to avoid over-replacing. If ambiguous, prefer the vocabulary term only when similarity is very high. |
| Same pronunciation, multiple vocabulary entries (e.g., "Read" and "Reed") | First match in vocabulary file wins. User should remove ambiguous entries. |
| Vocabulary file is empty or missing | Post-processing correction is skipped gracefully. Transcription proceeds normally. |
| LLM correction produces hallucinated content | The original transcript is always preserved. LLM prompt constrains output to corrections only. User can revert. |
| Ollama is not installed or not running | LLM correction button is disabled/hidden with a tooltip explaining the requirement. Phonetic correction still runs. |
| Very large vocabulary (>500 terms) | Phonetic matching performance may degrade. Log a warning. Consider indexing if this becomes an issue. |
| Thai term in vocabulary with English transliteration | PyThaiNLP romanization is used for phonetic comparison. Both Thai script and romanized forms should match. |
| Mixed Thai/English transcript | Phonetic matching applies the appropriate algorithm per word (English phonetics for Latin script, Thai phonetics for Thai script). |
| Vocabulary term appears as part of a compound word | Only whole-word matches are corrected. "Nimble" should not trigger correction of "nimbly." |
| LLM correction on a 2-hour transcript | Process in chunks to stay within model context limits. Show progress indicator. |

## Open Questions

| # | Question | Impact |
|---|----------|--------|
| 1 | Should phonetic correction run before or after Thai normalization? Running after may be more accurate since word boundaries are cleaner. | Pipeline ordering |
| 2 | What Ollama model balances quality vs. speed on M2 Air? `gemma3:4b` is the current default assumption — needs benchmarking. | Hardware feasibility |
| 3 | Should vocabulary terms support aliases or variants (e.g., "KBTG" = "Kasikorn Business Technology Group")? This adds complexity but could improve LLM correction context. | Feature complexity |
| 4 | Should the phonetic correction log show which words were replaced, for transparency? Could be shown in a collapsible section in the transcript viewer. | UX design |
| 5 | For Thai phonetic matching, is PyThaiNLP's romanization sufficient or do we need a dedicated Thai phonetic similarity algorithm? | Thai quality |

## Implementation Notes

**Suggested implementation order:**

1. **Vocabulary file + API** — File format, CRUD endpoints, vocabulary loading. Foundation for everything else.
2. **Vocabulary management UI** — Web page for managing terms. Can be used immediately even before post-processing exists.
3. **Phonetic post-processing (English)** — `jellyfish` Metaphone matching against vocabulary after transcription. Immediate quality improvement.
4. **Thai normalization** — PyThaiNLP word segmentation. Independent of phonetic matching.
5. **Phonetic post-processing (Thai)** — PyThaiNLP romanization for Thai phonetic matching. Builds on steps 3 and 4.
6. **LLM correction pass** — Ollama integration, transcript correction UI. Most complex, lowest priority.
