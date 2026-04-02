# Plan: Meeting Analysis Templates Refinement

**Story**: docs/specs/meeting-analysis-templates-refinement.md
**Spec**: docs/specs/meeting-analysis-templates-refinement.md
**Branch**: feature/meeting-analysis-templates-refinement
**Date**: 2026-04-02
**Mode**: Standard — Template content changes only; no testable code behaviors

## Technical Decisions

### TD-1: Replace templates in-place
- **Context**: Spec's open question about versioning during transition
- **Decision**: Replace templates in-place without versioning
- **Alternatives considered**: Adding v2 suffix to filenames; decided against per spec instruction "Template content changes only"

### TD-2: Include explicit word count guidance
- **Context**: Spec's concern about LLMs not reliably hitting length targets
- **Decision**: Include explicit word count targets in prompt instructions
- **Alternatives considered**: Relying solely on structural guidance; adding both for better compliance

### TD-3: Include confidence levels for interpretive observations
- **Context**: Spec's question about confidence calibration for nuanced interpretations
- **Decision**: Instruct LLM to rate confidence for "Intent vs. words" and "Potential Issues" observations
- **Alternatives considered**: Omitting confidence ratings; decided to include per spec edge case guidance

## Files to Create or Modify

- `templates/sales_meeting_analysis.md` — Complete rewrite with dual-output, tiered sections, effectiveness assessment, signal detection, and self-assessment
- `templates/client_meeting_analysis.md` — Complete rewrite with dual-output, tiered sections, effectiveness assessment, signal detection, and self-assessment
- `templates/other.md` — Complete rewrite with tiered sections, effectiveness assessment, signal detection, and self-assessment

## Approach per Goal

### Goal 1: Reduce template verbosity by 40-50%
- Remove redundant table structures
- Use bullets over tables where appropriate
- Combine similar sections
- Focus on actionable insights over exhaustive categorization

### Goal 2: Introduce tiered sections
- Mark each section as Required or Content-Dependent in template metadata
- Add explicit LLM instructions to omit content-dependent sections when insufficient signal

### Goal 3: Add client-shareable output (client template)
- Add dual-output structure: Internal Analysis + Client-Shareable Summary
- Include clear separation with content safety guidelines
- Never include sentiment, private observations, risks, potential issues in shareable output

### Goal 4: Add meeting effectiveness assessment
- Add four-dimension assessment framework (decision yield, data readiness, circular discussion, intent vs. words)
- Include behavioral change meta-principle
- Internal-facing only

### Goal 5: Create sales follow-up format (sales template)
- Add dual-output structure: Sales Intelligence + Prospect Follow-Up
- Include professional thank-you email format

### Goal 6: Enable personal performance tracking
- Add opt-in prompt at template start
- Include metrics, observations, patterns to watch
- Include Trackable Summary line format for longitudinal tracking

## Commit Sequence

1. `Refine sales meeting analysis template` — Add dual-output, tiered sections, effectiveness assessment, contribution analysis, signal detection, self-assessment, potential issues
2. `Refine client meeting analysis template` — Add dual-output, tiered sections, effectiveness assessment, contribution analysis, signal detection, self-assessment, potential issues
3. `Refine general meeting analysis template` — Add tiered sections, effectiveness assessment, contribution analysis, signal detection, self-assessment, potential issues

## Risks and Trade-offs

- **LLM compliance**: Templates are instructions, not code; LLM behavior may vary. Mitigated by clear, explicit instructions.
- **Length targets**: LLMs may not hit exact word counts. Mitigated by structural guidance + explicit word count notes.
- **Breaking user expectations**: Users familiar with old format will see new output structure. This is an intentional improvement per the spec.

## Deviations from Spec

_None planned._

## Deviations from Plan

- Added explicit handling for "transcript-only limitations" edge case (spec requirement, discovered during QA)
- Added explicit handling for "self-assessment speaker not found" edge case (spec requirement, discovered during QA)
