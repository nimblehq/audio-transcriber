# Plan: Warn on Analysis tab when speakers are unnamed

**Story**: #74
**Spec**: N/A
**Branch**: feature/74-warn-unnamed-speakers-on-analysis
**Date**: 2026-05-29
**Mode**: Standard — small vanilla JS/CSS change; project has no frontend test framework, no need for TDD scaffolding.

## Technical Decisions

### TD-1: Reuse `.overview-notice` CSS class instead of introducing `.analysis-warning`
- **Context**: The Analysis tab needs a visual banner; `.overview-notice` already provides the exact look (warning-colored left border, surface background, muted text) used by the Overview tab.
- **Decision**: Reuse `.overview-notice` directly on the Analysis tab banner.
- **Alternatives considered**: A parallel `.analysis-warning` class — rejected to avoid visual drift between two identical banners (Architect Minor finding).

### TD-2: Read unnamed-speaker info from `window._speakerEditorState`
- **Context**: The transcript viewer already computes `speakers` and `speakerIds` and stashes them on a global state bag. Re-deriving from the meeting object would duplicate logic.
- **Decision**: Read `window._speakerEditorState` in `analysis-viewer.js` with an inline comment documenting the dependency on `transcript-viewer.renderSegments()`.
- **Alternatives considered**: Re-fetching from a `currentMeeting` global — none exists; would require a new global.

### TD-3: Show the warning both before and after Generate Prompt
- **Context**: After generation the prompt UI replaces the generator UI. Hiding the warning at that point would let users copy the prompt without seeing that it still contains raw `SPEAKER_xx` labels.
- **Decision**: Render the warning in both `renderAnalysisTab` (initial) and `renderPromptContent` (post-generate).
- **Alternatives considered**: Hide post-generate — rejected; the warning is more useful precisely when the user is about to copy the prompt.

## Files to Create or Modify

- `frontend/js/components/analysis-viewer.js` — add helpers `getUnnamedSpeakersInfo()` and `renderUnnamedSpeakersWarning()`; prepend the banner in both render functions.
- `frontend/css/styles.css` — no new class; if a tab-context margin override is needed, add a one-liner.

## Approach per AC

### AC: Warning visible on the Analysis tab when speakers are not labeled
- On Analysis tab render, count speakers in `window._speakerEditorState.speakerIds` where `isUnidentifiedSpeaker(state.speakers[id] || id)` is true.
- If `unnamed > 0`, render an `.overview-notice` banner at the top with a sentence explaining the impact and pointing users to the Transcript tab.
- If `unnamed === 0` or state is missing, render nothing.

## Commit Sequence

1. `[#74] Warn on analysis tab when speakers are unnamed`

## Risks and Trade-offs

- Cross-component read of `window._speakerEditorState` couples `analysis-viewer.js` to `transcript-viewer.js` lifecycle. Mitigated by an inline comment so a future refactor flags the dependency.
- Persistent warning after Generate Prompt is intentional (see TD-3). Worth a note in the PR description so reviewers don't read it as accidental duplication.

## Deviations from Plan

_Populated after implementation._
