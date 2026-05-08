# Plan — Story #53: Audio insights in transcript viewer + Overview tab

## Files
- Backend: `backend/schemas.py`, `backend/routers/meetings.py`, `tests/integration/test_meetings.py`
- Frontend: `frontend/js/components/transcript-viewer.js`, `frontend/js/components/overview-viewer.js` (new), `frontend/index.html`, `frontend/css/styles.css`

## Commits
1. `[#53] Expose audio_analysis in meeting detail API`
2. `[#53] Render inline emotion, prosody, mismatch, and interaction indicators on transcript segments`
3. `[#53] Add Overview tab with trajectory chart and interaction summary`

## Decisions
- Standard mode (not strict TDD): backend gets integration tests; frontend is browser-smoke-tested.
- Word-tone mismatch detection replicated in JS (mirrors `backend/services/analysis_context.py` AGREEMENT_PHRASES + MISMATCH_EMOTIONS). Acceptable JS↔Py drift risk; revisit if list grows.
- Prosody summary surfaced via `title` attribute (no custom tooltip popover).
- Backward compat gate: `audio_analysis_enabled === true` AND `audio_analysis?.status === "completed"`. No try/catch.
- Overview chart is inline SVG (no dependency) reusing the energy-score logic from backend (positive: engaged/confident, negative: disengaged/frustrated).

## Risks
- Word-tone mismatch JS↔Py drift if AGREEMENT_PHRASES expands.
- `title` tooltips have minimal styling control (acceptable).
