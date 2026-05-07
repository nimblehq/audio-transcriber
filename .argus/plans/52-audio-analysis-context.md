# Plan — #52 Audio Analysis Context in Analysis Prompts

## Approach

Server-side context generation. New endpoint `GET /api/meetings/{id}/analysis-context` returns the rendered Audio Analysis Context markdown (empty string when opted out → byte-identical prompt to today's, satisfying BR-4.4).

Frontend fetches the context alongside the template and substitutes a `[AUDIO ANALYSIS CONTEXT]` placeholder.

## Files

- `backend/services/analysis_context.py` (new) — pure functions assembling the context markdown.
- `backend/routers/analysis.py` — add endpoint.
- `templates/{interview,sales,client,other}_analysis.md` (`other.md`) — add placeholder before `## Transcript`. Skip `prototype_scope.md`.
- `frontend/js/api.js` — `getAnalysisContext`.
- `frontend/js/components/analysis-viewer.js` — fetch + substitute.
- `tests/unit/test_analysis_context.py` (new).
- `tests/integration/test_analysis_context.py` (new).

## Heuristics

- **Word-tone mismatch:** transcript text matches a small positive-agreement lexicon (`works for me`, `sounds good`, `that's fine`, `no concerns`, `agreed`, `sure thing`, `fine by me`, `okay`) AND emotion is `frustrated`/`uncertain` with confidence ≥ 0.5. Confidence < 0.5 → hedged ("may indicate"); ≥ 0.5 → asserted ("indicates").
- **Emotional spikes:** per-speaker, list timestamps where emotion is `frustrated` or `uncertain` with confidence ≥ 0.7.
- **Energy trajectory:** 5-minute windows. Score per segment: engaged/confident = +1 × confidence, disengaged/frustrated = -1 × confidence, neutral/uncertain = 0. Surface peak window and trough window.
- **Hedging:** below 0.5 confidence triggers "possibly", "may indicate".
- **Single-speaker dominance:** if `dominant_speaker_limitation` true, append explicit note in Interaction Dynamics section.

## Commits

1. service + unit tests
2. endpoint + integration tests
3. template placeholder updates
4. frontend wiring

## Mode

Standard (test-alongside, not strict TDD). Heuristics are tunable.
