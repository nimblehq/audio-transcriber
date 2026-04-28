# General Meeting Analysis Template

## Template Metadata

**Purpose:** Generate structured summary for any meeting type
**Target length:** ~300-400 words
**Output structure:** Single output (internal analysis)

### Section Classification

| Section | Tier | Notes |
|---------|------|-------|
| Summary | Required | Always include |
| Decisions | Required | Always include (note "none" if applicable) |
| Action Items | Required | Always include |
| Meeting Effectiveness | Required | Always include |
| Key Discussion Points | Content-dependent | Include if substantive topics discussed |
| Contribution Dynamics | Content-dependent | Include if notable patterns |
| Meeting Signals | Content-dependent | Include if notable signals detected |
| Potential Issues | Content-dependent | Include if issues detected |
| Your Contribution | Content-dependent | Only if user opts in |

## Prompt

You are analyzing a meeting transcript. Extract key information in a clear, actionable format.

**Attendees:** [identified from transcript]
**Date:** [today or extracted from context]

### Personal Performance Opt-In

Before analyzing, I have a question:

Would you like me to include a personal performance analysis of your own contribution to this meeting? This section analyzes your talk time, question quality, hedging patterns, and other behaviors to support self-improvement tracking over time.

[ ] Yes, include my performance analysis
[ ] No, skip this section

If yes: What name or speaker label identifies you in the transcript?
[Your name]: _______

### Instructions

Analyze the transcript and produce a structured summary. Target ~300-400 words total.

**Key principles:**
- Focus on what was discussed, decided, and what needs to happen next
- Cite evidence from the conversation where relevant
- Use "In this meeting..." not "This group has..." for single-meeting observations
- Volume ≠ value: Don't assume the person who spoke most was most important
- Omit content-dependent sections entirely if insufficient signal
- Include confidence levels for interpretive observations (high/medium/low)
- Acknowledge transcript-only limitations: When tone would materially affect interpretation (e.g., "that's fine" could be agreement or frustration), note that audio context would clarify

**For commitment assessment, use this spectrum:**
- **Strong:** "I will deliver X by Friday" (clear verb, owner, deadline)
- **Moderate:** "I'll look into that this week" (owner, rough timeline, vague deliverable)
- **Weak:** "We should explore this" (no owner, no timeline)
- **Empty:** "Someone needs to handle that" (diffusion of responsibility)

### Output Format

```markdown
# Meeting Summary

**Date:** {{DATE}} | **Duration:** [from transcript]
**Attendees:** [Names identified in transcript]

## Summary

[3-5 sentences: Meeting purpose, key takeaway, any notable outcomes]

## Decisions

| Decision | Context |
|----------|---------|
| [What was decided] | [Why or relevant context] |

[If no decisions: "No explicit decisions made in this meeting."]

## Action Items

- [Task] — Owner: [Name] — Due: [Date/TBD] — Strength: Strong/Moderate/Weak

## Meeting Effectiveness

**Behavioral change estimate:** [X]% of this meeting will drive changed actions
- **Decision yield:** [Assessment if relevant — decisions made vs. time spent?]
- **Data readiness:** [Assessment if relevant — was blocking information missing?]
- **Circular discussion:** [Assessment if relevant — topics revisited without new info?]
- **Intent vs. words:** [Assessment if relevant — signs of unstated concerns?] (Confidence: high/medium/low)

[Omit dimensions with insufficient evidence]

## Key Discussion Points
[CONTENT-DEPENDENT: Include only if substantive topics discussed]

### [Topic 1]
[Summary of what was discussed and any conclusions]

### [Topic 2]
[Summary of what was discussed and any conclusions]

## Contribution Dynamics
[CONTENT-DEPENDENT: Include only if notable patterns detected]

- **Progress drivers:** [Who moved things forward, with evidence]
- **Airtime/impact mismatch:** [High airtime + low impact, or low airtime + high impact]
- **40% threshold:** [Flag any speaker who consumed >40% of talk time]
- **Patterns:** [Assertion vs. persuasion, listening signals, position changes]

## Meeting Signals
[CONTENT-DEPENDENT: Include only categories with notable patterns]

**Question quality:** [Types asked, distribution, unanswered questions]
**Hedging patterns:** [Who hedges, in what contexts, correlation with unresolved topics]
**Convergence quality:** [Did they explore alternatives? Early anchoring? Groupthink risk?]
**Commitment clarity:** [Ratio of strong to weak commitments, accountability gaps]
**Topic drift:** [Time on tangents, who brought it back, unaddressed agenda items]

## Potential Issues
[CONTENT-DEPENDENT: Include only if issues detected]

- **[Category]:** [Description] — Evidence: "[quote]" — Suggested follow-up: [Action]

Categories: Confusion | Misunderstanding | Hidden Disagreement | Unresolved

## Your Contribution ([Speaker Name])
[CONTENT-DEPENDENT: Include only if user opted in AND speaker found in transcript]

**If speaker not found:** Instead of this section, output:
"I couldn't find '[provided name]' in the transcript. The speakers I found are: [list speaker names/labels]. Please clarify which speaker you are, and I'll regenerate the self-assessment."

### Metrics
- Talk time: ~XX%
- Questions asked: X (X clarifying, X challenging, X leading)
- Ideas adopted: X
- Progress driver: Yes/No — [brief evidence]

### Observations
- **Hedging:** [None detected / X instances — context]
- **Interruptions:** [Interrupted others X times / Was interrupted X times]
- **Commitments:** [Strong/Moderate/Vague] — [examples]
- **Listening:** [Built on others' points / Primarily advanced own ideas]

### Patterns to Watch
- [Specific observation for self-improvement]

### Trackable Summary
`XX% talk | XQ | X adopted | driver:[y/n] | hedge:X | commits:[s/m/v]`
```

## Transcript

[MEETING CONTEXT]

[PASTE TRANSCRIPT HERE]
