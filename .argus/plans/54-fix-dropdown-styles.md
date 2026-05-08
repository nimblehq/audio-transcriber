# Plan: Fix dropdown field styles (#54)

## Problem
- `<select>` height does not match `<input>` height in `.form-group` rows.
- Native caret has insufficient right padding / odd alignment.

## Approach
- Suppress native select chrome via `appearance: none` (+ vendor prefixes).
- Render a custom SVG chevron through `background-image` with `right 12px center` positioning.
- Add `padding-right: 36px` to leave room for the chevron.
- Apply the same treatment to `.player-speed select` (smaller variant) for consistency.
- Provide a theme-aware chevron color (override under `[data-theme="light"]`).

## Files
- `frontend/css/styles.css`

## Commits
- `[#54] Fix dropdown field height and caret alignment`

## Verification
- Visual check on `/upload` (dark + light themes): select height matches input, caret has clear right padding.
- Visual check on transcript viewer playback speed dropdown.
