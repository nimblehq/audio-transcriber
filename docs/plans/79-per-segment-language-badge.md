# Plan: See which language each segment was detected as

**Story**: 79
**Spec**: docs/specs/multilingual-transcription.md
**Branch**: feature/79-per-segment-language-badge
**Date**: 2026-06-10
**Mode**: Standard — no JS test harness exists (vanilla JS, `package.json` is release-tooling only, conventions state "No frontend linter/test"); ACs verified via manual run + QA agent.

## Technical Decisions

### TD-1: Single source of truth for language code → display name
- **Context**: A code→name mapping already exists implicitly as 18 hardcoded `<option>` entries in `upload.js`. The badge needs the same mapping. The Architect's first review caught that duplicating only `en`/`th` would fail AC1 for the 16 other selectable languages.
- **Decision**: Add `LANGUAGE_NAMES` (all 18 codes) and `formatLanguageName(code)` to `utils.js`, and have `upload.js` render its `<option>` list from that map. One authoritative representation; no drift.
- **Alternatives considered**: (a) Duplicate a full 18-entry map in both places with sync comments — rejected, drift-prone (it already drifted once). (b) Map only en/th — rejected, fails AC1 for other languages.

### TD-2: Honest fallback title for EC-8
- **Context**: Legacy/un-analyzed segments have no per-segment language and fall back to the meeting primary (default `"en"`). Presenting that as a definite per-segment detection would overstate confidence.
- **Decision**: Badge text is the resolved language name either way (truth: badge names the segment's language, falling back to meeting language). The `title` tooltip distinguishes `Detected language: {name}` (segment carries its own language) from `Meeting language: {name}` (EC-8 fallback).
- **Alternatives considered**: Mute the badge visually (emotion-badge-muted precedent) — deferred as unnecessary visual noise; the title distinction is enough.

## Files to Create or Modify

- `frontend/js/utils.js` — add `LANGUAGE_NAMES` (18 codes) + `formatLanguageName(code)` (mapped name, else uppercased code for unknown non-empty code, else `''`).
- `frontend/js/components/upload.js` — generate the language `<option>` list from `LANGUAGE_NAMES` (insertion order preserves en/th-first ordering).
- `frontend/js/components/transcript-viewer.js` — render a per-segment `.language-badge` in `.segment-header` after the speaker label; resolve `seg.language || transcript.language`; escapeHtml text + title.
- `frontend/css/styles.css` — add `.language-badge` styled like `.emotion-badge` (outlined pill, theme vars).

## Approach per AC

### AC1: Each segment header shows a badge naming the segment's detected language.
Compute `meetingLanguage = transcript.language` once in `renderSegments`; per segment `segLang = seg.language || meetingLanguage`, `langName = formatLanguageName(segLang)`. Render the badge when `langName` is non-empty. All 18 selectable languages map to a name; unknown codes degrade to the uppercased code.

### AC2: Legacy segment with no stored language falls back to the meeting's primary detected language (EC-8).
`seg.language === null` → `transcript.language` (the meeting primary). No metadata migration.

### AC3: Copy/export output unchanged — badge not in copied text (OQ-5).
Badge lives in `.segment-header`, not `.segment-text`. `renderPlainTextTab` reads only `.segment-time` / `.speaker-label` / `.segment-text`, so it never picks up the badge. No copy-logic change.

## Commit Sequence

1. Add shared `LANGUAGE_NAMES` map + `formatLanguageName` to utils.js; render upload.js options from it.
2. Render per-segment language badge in transcript viewer + CSS.

## Risks and Trade-offs

- Unknown/future language codes degrade gracefully to the uppercased code rather than failing.
- EC-8 fallback presents the meeting primary (default `"en"`) for legacy/un-analyzed segments; the title says "Meeting language:" to avoid asserting a per-segment detection that never happened.
- `upload.js` option generation is a low-risk render change; ordering preserved via object insertion order.

## Deviations from Spec

- None. Badge is UI-only (OQ-5), defaults to meeting primary for legacy segments (EC-8), and reflects per-segment stored language (BR-12).

## Deviations from Plan

- None. Implementation followed the approved plan exactly: shared `LANGUAGE_NAMES` map + `formatLanguageName` in utils.js, upload.js options generated from the map, `renderLanguageBadge` in the transcript viewer, and `.language-badge` CSS. Architect code review passed with no Critical/Major findings.
