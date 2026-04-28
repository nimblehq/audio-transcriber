# Plan: Refine Meeting Analysis

**Story**: #39
**Spec**: N/A
**Branch**: feature/39-refine-meeting-analysis
**Date**: 2026-04-28
**Mode**: Standard — markdown prompt templates, no automated tests apply.

## Technical Decisions

### TD-1: Include heuristic guidance, not just observation
- **Context**: The new signals (next-action initiator, banter) only become useful if the LLM weights them in its assessment, not just collects them.
- **Decision**: Each new field includes a short heuristic note explaining the signal (e.g., "prospect-driven next steps = positive buying signal", "banter generally indicates engagement").
- **Alternatives considered**: Collect the data points neutrally and let downstream readers interpret. Rejected — the issue body explicitly frames these as positive signals; encoding the heuristic makes the output actionable.

### TD-2: Sales template gets both signals prominently; client/other get rapport only
- **Context**: Issue #39 ties next-action driver specifically to sales context. For client meetings (existing engagement) it carries less buying-signal weight.
- **Decision**: Sales template surfaces next-step driver in Deal Snapshot and rapport in Prospect Sentiment. Client template adds rapport to Client Sentiment + a lightweight next-step driver line in Action Items. Other template adds rapport only to Meeting Signals.
- **Alternatives considered**: Add both fields uniformly across all templates. Rejected — would dilute the sales-specific intent and add length to non-sales outputs.

### TD-3: Rapport stays content-dependent / part of existing sentiment sections
- **Context**: Recent refinement spec emphasized reducing verbosity. New signals risk re-bloating output.
- **Decision**: No new top-level sections — rapport piggybacks on existing Sentiment sections (sales, client) or Meeting Signals (other). Next-step driver is a single line inside Deal Snapshot / Action Items.
- **Alternatives considered**: Add a dedicated "Engagement Signals" section. Rejected — adds structural overhead for two short fields.

## Files to Create or Modify

- `templates/sales_meeting_analysis.md` — add next-step driver to Deal Snapshot, rapport to Prospect Sentiment, update Section Classification, add heuristic to Key principles.
- `templates/client_meeting_analysis.md` — add rapport to Client Sentiment, next-step driver line to Action Items.
- `templates/other.md` — add rapport line to Meeting Signals.

## Approach per AC

The issue itself only carries two bullet points (no formal AC). They map directly:

### "Who's pushing for next actions? For sales meetings, if it's the client, it's a positive."
Sales template: Deal Snapshot gets `**Next-step driver:** Prospect / Us / Mutual — Evidence: ...`. Heuristic line in Key principles notes prospect-driven next steps as a positive buying signal. Client template gets a lighter version in Action Items.

### "Banter is usually a good sign."
Sales template: rapport line in Prospect Sentiment with banter as evidence example. Client template: rapport line in Client Sentiment. Other template: rapport line in Meeting Signals. All three include the heuristic that banter generally indicates engagement.

## Commit Sequence

1. `[#39] Add next-step driver and rapport signals to sales template`
2. `[#39] Add rapport signal to client template`
3. `[#39] Add rapport signal to general meeting template`
4. `[#39] Add plan document for issue #39`

## Risks and Trade-offs

- Slight length increase contradicts the verbosity-reduction spec. Mitigation: each addition is a single line inside an existing section; rapport sections remain content-dependent (omit if no signal).
- "Rapport" is interpretive. Mitigation: existing template principles already require confidence levels for interpretive observations — that guidance applies here.
- Heuristic encoding risks LLM over-confirming the heuristic (confirmation bias). Mitigation: heuristics phrased as "generally" / "often", not "always".

## Deviations from Plan

_Populated after implementation._
