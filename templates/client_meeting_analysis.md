# Client Meeting Analysis Template

## Template Metadata

**Purpose:** Extract project decisions, action items, and generate client-shareable summary
**Target length:** Internal Analysis ~400-500 words | Client-Shareable Summary ~200-300 words
**Output structure:** Dual-output (internal notes + external summary)

### Section Classification

| Section | Tier | Notes |
|---------|------|-------|
| Summary | Required | Always include |
| Decisions | Required | Always include (note "none" if applicable) |
| Action Items | Required | Always include |
| Meeting Effectiveness | Required | Internal only |
| Project Status | Content-dependent | Include if progress/blockers discussed |
| Technical Discussions | Content-dependent | Include if technical topics covered |
| Client Sentiment | Content-dependent | Internal only; include if sentiment signals detected |
| Contribution Dynamics | Content-dependent | Include if notable patterns |
| Meeting Signals | Content-dependent | Include if notable signals detected |
| Potential Issues | Content-dependent | Include if issues detected |
| Your Contribution | Content-dependent | Only if user opts in |
| Client-Shareable Summary | Required | Always generate |

### Client-Shareable Content Safety

The Client-Shareable Summary must NEVER include:
- Client sentiment analysis or mood assessments
- Private observations about client behavior or politics
- Risk assessments about the client relationship
- Potential Issues section content
- Meeting Effectiveness assessment
- Contribution Dynamics analysis
- Any content from internal-only sections

## Prompt

You are analyzing a client meeting transcript for Nimble, a digital product consulting company. This is an ongoing engagement covering project status, planning, and/or problem-solving.

**Client:** {{CLIENT_NAME}}
**Project:** {{PROJECT_NAME}}
**Attendees:** {{NAMES_AND_ROLES}}
**Date:** {{DATE}}

### Personal Performance Opt-In

Before analyzing, I have a question:

Would you like me to include a personal performance analysis of your own contribution to this meeting? This section analyzes your talk time, question quality, hedging patterns, and other behaviors to support self-improvement tracking over time.

[ ] Yes, include my performance analysis
[ ] No, skip this section

If yes: What name or speaker label identifies you in the transcript?
[Your name]: _______

### Instructions

Extract key information for project management and follow-up. Target ~400-500 words for Internal Analysis and ~200-300 words for Client-Shareable Summary.

**Key principles:**
- Be precise: decided vs. discussed vs. open
- Attribute action items to specific people with deadlines
- Use "In this meeting..." not "This team has..." for single-meeting observations
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
# Internal Analysis: {{CLIENT_NAME}} — {{PROJECT_NAME}}

**Date:** {{DATE}} | **Duration:** [from transcript]
**Attendees:** [Names — Company]

## Summary

[3-5 sentences: Meeting purpose, headline outcome, any major shifts or concerns]

## Decisions

| Decision | Context |
|----------|---------|
| [What was decided] | [Why, if discussed] |

[If no decisions: "No explicit decisions made in this meeting."]

## Action Items

**Nimble:**
- [Task] — Owner: [Name] — Due: [Date/TBD] — Strength: Strong/Moderate/Weak

**Client:**
- [Task] — Owner: [Name] — Due: [Date/TBD] — Strength: Strong/Moderate/Weak

## Meeting Effectiveness

**Behavioral change estimate:** [X]% of this meeting will drive changed actions
- **Decision yield:** [Assessment if relevant — decisions made vs. time spent?]
- **Data readiness:** [Assessment if relevant — was blocking information missing?]
- **Circular discussion:** [Assessment if relevant — topics revisited without new info?]
- **Intent vs. words:** [Assessment if relevant — signs of unstated concerns?] (Confidence: high/medium/low)

[Omit dimensions with insufficient evidence]

## Project Status
[CONTENT-DEPENDENT: Include only if progress or blockers discussed]

**Progress:** [What was completed or advanced]

**Blockers:**
- [Issue] — Impact: High/Med/Low — Owner: [Name] — Resolution path: [What needs to happen]

**Upcoming milestones:**
- [Milestone] — Target: [Date] — Status: On Track / At Risk / Blocked

**Scope changes:** [Additions, removals, deferrals if discussed]

## Technical Discussions
[CONTENT-DEPENDENT: Include only if technical topics covered]

**Decisions:** [Technical decisions made]
**Open:** [Topics needing more exploration]

## Client Sentiment
[CONTENT-DEPENDENT: Internal only — include if clear sentiment signals detected]

- **Overall mood:** Positive / Neutral / Concerned / Frustrated
- **Project confidence:** High / Moderate / Low
- **Key concerns:** [What's on their mind?]
- **Notable quotes:** "[Anything important worth remembering]"

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

## Private Notes

[Internal observations not for client: relationship dynamics, concerns, politics to navigate]

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

---

# Client-Shareable Summary

[Professional summary suitable for emailing to clients, ~200-300 words]

## Meeting Summary: {{PROJECT_NAME}}

**Date:** {{DATE}}
**Attendees:** [Names]

### Overview

[2-3 sentences: What we covered and key outcomes]

### Decisions Made

- [Decision 1]
- [Decision 2]

[Omit this section entirely if no decisions were made]

### Action Items

**Nimble will:**
- [Task] — [Owner] — [Timeline]

**[Client] will:**
- [Task] — [Owner] — [Timeline]

### Next Steps

[What happens next, when we'll reconnect]

---
*Summary prepared by Nimble*
```

## Transcript

[MEETING CONTEXT]

[PASTE TRANSCRIPT HERE]
