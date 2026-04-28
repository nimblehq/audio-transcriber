# Plan: Sticky audio player at top when scrolling transcript

**Story**: #7
**Spec**: N/A
**Branch**: feature/7-sticky-audio-player
**Date**: 2026-04-28
**Mode**: Standard — pure CSS change; no test harness for visual behavior in this project.

## Technical Decisions

### TD-1: Use CSS `position: sticky` on `.audio-player`
- **Context**: The audio player should remain visible while the user scrolls through transcript segments so playback controls stay accessible.
- **Decision**: Apply `position: sticky; top: 0; z-index: 10;` to `.audio-player`. The viewport is the scrolling ancestor (`#app` does not scroll), so the player pins to the top of the window once scrolled past.
- **Alternatives considered**:
  - `position: fixed`: would require manually reserving space and managing width to match the `#app` container; sticky avoids that.
  - JS-based scroll listener: unnecessary complexity for a behavior CSS handles natively.

### TD-2: Keep existing opaque background and add a subtle shadow
- **Context**: When the player overlays scrolled segments, transparent edges or no separation would feel jarring.
- **Decision**: The existing `background: var(--bg-surface)` is fully opaque. Add a soft `box-shadow` so the player visually separates from segments below when stuck.
- **Alternatives considered**: Toggling a class via IntersectionObserver to add the shadow only when stuck — adds JS for marginal polish; skipped.

## Files to Create or Modify

- `frontend/css/styles.css` — add `position: sticky; top: 0; z-index: 10;` and a soft `box-shadow` to `.audio-player`.

## Approach per AC

### AC: Audio player sticks at the top when scrolling down the transcript
Pin `.audio-player` via CSS `position: sticky` against the viewport. Tabs and segments scroll underneath while controls remain reachable.

## Commit Sequence

1. `[#7] Add plan document for issue #7`
2. `[#7] Make audio player sticky at top when scrolling transcript`

## Risks and Trade-offs

- **Speaker editor popover**: opens relative to a segment and could be clipped beneath the sticky player when near the top. Acceptable — the popover already scrolls into view via clicks, and users can scroll segment into view first.
- **Mobile**: existing `@media (max-width: 640px) .audio-player { flex-wrap: wrap }` is compatible with sticky; on small screens the player will be taller but still pin correctly.
- **Z-index**: theme toggle uses `position: fixed; z-index: 999` and floats freely; no overlap conflict.

## Deviations from Plan

_Populated after implementation._
