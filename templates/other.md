# General Meeting Analysis Template

Use this prompt with a meeting transcription to generate a structured summary.

## Prompt

You are analyzing a meeting transcript. Extract the key information in a clear, actionable format.

**Attendees:** [identified from transcript]
**Date:** [today or extracted from context]

### Instructions

Analyze the transcript and produce a structured summary. Be specific — cite examples from the conversation where relevant. Focus on what was discussed, decided, and what needs to happen next.

### Output Format

```markdown
# Meeting Summary

**Date:** [Date]
**Duration:** [extracted from transcript]
**Attendees:** [Names identified in transcript]

## Summary

[3-5 sentences: What was this meeting about? What's the key takeaway?]

## Key Discussion Points

### [Topic 1]
[Summary of what was discussed]

### [Topic 2]
[Summary of what was discussed]

## Decisions Made

| # | Decision | Context |
|---|----------|---------|
| 1 | [What was decided] | [Why or relevant context] |

## Action Items

| # | Action | Owner | Deadline | Notes |
|---|--------|-------|----------|-------|
| 1 | [Task] | [Name] | [Date or TBD] | [Context] |

## Open Questions

| # | Question | Owner | Context |
|---|----------|-------|---------|
| 1 | [Unresolved question] | [Who needs to answer] | [Background] |

## Notable Quotes

> "[Important or memorable statement]"
> — [Speaker name]
```

## Transcript

[PASTE TRANSCRIPT HERE]
