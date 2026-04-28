# Plan: Find Unidentified Speakers

**Story**: #43
**Spec**: N/A
**Branch**: feature/43-find-unidentified-speakers
**Date**: 2026-04-28
**Mode**: Standard — UI-only frontend change; no backend test framework targets vanilla JS, manual browser verification.

## Technical Decisions

### TD-1: Detect "unidentified" speakers by mapped name pattern
- **Context**: Need to flag speakers the user hasn't labeled yet.
- **Decision**: A speaker is "unidentified" when its mapped name (from `metadata.speakers[id]`) still equals the raw diarization label, i.e. matches `/^SPEAKER_\d+$/` or equals `UNKNOWN`. Once renamed, it's no longer flagged.
- **Alternatives considered**: Tracking a `labeled` boolean per speaker on the backend — rejected because it requires schema changes and migrations for a UI-only problem; the existing data model already encodes the state implicitly.

### TD-2: Right-side floating panel instead of a top sticky bar
- **Context**: A sticky bar at the top would compound visual clutter (the audio player is already sticky). The 960px main column leaves whitespace to the right on wide viewports.
- **Decision**: Fixed-position sidebar docked to the right of the main column on wide viewports (≥1100px); collapses to a floating button bottom-right on narrow viewports.
- **Alternatives considered**: Sticky top bar (rejected — too much vertical clutter); inline panel above segments (rejected — scrolls out of view, defeats the purpose).

### TD-3: Click-to-jump opens the rename popover
- **Context**: The point of finding an unidentified speaker is to label them.
- **Decision**: Clicking a sidebar entry scrolls to that speaker's first segment and immediately opens the existing `openSpeakerEditor` popover.
- **Alternatives considered**: Just scrolling — wastes a click; the user always wants to edit after finding.

## Files to Create or Modify

- `frontend/js/components/transcript-viewer.js` — render sidebar markup, build speaker list from segments, wire up click handlers, manage visibility per tab, re-render after rename.
- `frontend/js/utils.js` — add `isUnidentifiedSpeaker(name)` helper.
- `frontend/css/styles.css` — sidebar layout, unnamed-state styling, responsive collapse, floating button variant.

## Approach per AC

### AC 1: User can see at a glance how many speakers are still unnamed
Sidebar header shows `Speakers — N of M unnamed` (or just `M speakers, all named` when none are unnamed). Counter updates whenever the user saves a rename.

### AC 2: User can jump to any speaker's segments without scrolling
Each sidebar entry is clickable. Click → `scrollIntoView({ block: 'center' })` on the first segment for that speaker, then `openSpeakerEditor` is invoked on that segment.

### AC 3: Sidebar stays visible while scrolling (does not require scrolling to find)
Wide viewports: `position: fixed`, vertically near the top of the viewport, anchored to the right of the `#app` column.
Narrow viewports: collapses to a floating button bottom-right (above the existing `back-to-top` button); clicking opens an overlay panel.

### AC 4: Sidebar appears only on the Transcript tab
Toggled via a class on a wrapper element when `switchTab` runs (Transcript on, Plain Text / Analysis off).

## Commit Sequence

1. `[#43] Add isUnidentifiedSpeaker helper`
2. `[#43] Add speakers sidebar to transcript viewer`
3. `[#43] Style sidebar with responsive collapse to floating panel`

## Risks and Trade-offs

- A real speaker name that looks like `SPEAKER_1` would be flagged as unnamed. Vanishingly unlikely in practice; not worth defending against.
- Floating UI on narrow viewports stacks with the existing `back-to-top` button. Mitigation: position the speakers FAB above `back-to-top` so neither obscures the other.

## Deviations from Plan

_Populated after implementation._
