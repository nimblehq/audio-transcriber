# Sales Meeting Analysis Template

## Template Metadata

**Purpose:** Extract sales intelligence and generate prospect follow-up from sales conversations
**Target length:** Sales Intelligence ~400-500 words | Prospect Follow-Up ~150-200 words
**Output structure:** Dual-output (internal intelligence + external follow-up)

### Section Classification

| Section | Tier | Notes |
|---------|------|-------|
| TL;DR | Required | Always include |
| Deal Snapshot | Required | Always include |
| Pain Points & Needs | Required | Always include |
| Commitments | Required | Always include |
| Meeting Effectiveness | Required | Internal only |
| Decision Making | Content-dependent | Include if buying process discussed |
| Budget Signals | Content-dependent | Include if budget/pricing discussed |
| Objections | Content-dependent | Include if concerns raised |
| Prospect Sentiment | Content-dependent | Include if sentiment signals detected |
| Contribution Dynamics | Content-dependent | Include if notable patterns |
| Meeting Signals | Content-dependent | Include if notable signals detected |
| Potential Issues | Content-dependent | Include if issues detected |
| Your Contribution | Content-dependent | Only if user opts in |
| Prospect Follow-Up | Required | Always generate |

## Prompt

You are analyzing a sales meeting transcript for Nimble, a digital product consulting company offering web/mobile development, UX/UI design, and product management services.

**Meeting type:** {{DISCOVERY / PROPOSAL / NEGOTIATION / FOLLOW-UP}}
**Prospect company:** {{COMPANY_NAME}}
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

Extract actionable sales intelligence from this conversation. Target ~400-500 words for Sales Intelligence and ~150-200 words for Prospect Follow-Up.

**Key principles:**
- Distinguish explicit statements from inferences (mark inferences clearly)
- Use "In this meeting..." not "This prospect has..." for single-meeting observations
- Volume ≠ value: Don't assume the person who spoke most was most important
- Omit content-dependent sections entirely if insufficient signal (don't fabricate)
- Include confidence levels for interpretive observations (high/medium/low)
- Acknowledge transcript-only limitations: When tone would materially affect interpretation (e.g., "that's fine" could be agreement or frustration), note that audio context would clarify

**For commitment assessment, use this spectrum:**
- **Strong:** "I will deliver X by Friday" (clear verb, owner, deadline)
- **Moderate:** "I'll look into that this week" (owner, rough timeline, vague deliverable)
- **Weak:** "We should explore this" (no owner, no timeline)
- **Empty:** "Someone needs to handle that" (diffusion of responsibility)

### Output Format

```markdown
# Sales Intelligence: {{COMPANY_NAME}}

**Date:** {{DATE}} | **Type:** {{TYPE}} | **Duration:** [from transcript]
**Attendees:** [Names — Company]

## TL;DR

[3-4 sentences: Opportunity summary, current position, critical next step]

## Deal Snapshot

- **Opportunity:** [What they need]
- **Size signals:** [Budget, team size, duration if discussed]
- **Timeline:** [When they want to start, deadline pressures]
- **Stage:** Discovery / Qualified / Proposal / Negotiation / Verbal Yes
- **Temperature:** Hot / Warm / Cool

## Pain Points & Needs

[What problems are they solving? Why now?]

- [Pain point 1] — Severity: High/Med/Low — Evidence: "[quote or paraphrase]"
- [Pain point 2] — Severity: High/Med/Low — Evidence: "[quote or paraphrase]"

**Underlying motivation:** [Business pressure, competitive threat, new leadership, etc.]

## Commitments

**We committed to:**
- [Action] — Owner: [Name] — Due: [Date/TBD] — Strength: Strong/Moderate/Weak

**They committed to:**
- [Action] — Owner: [Name] — Due: [Date/TBD] — Strength: Strong/Moderate/Weak

## Meeting Effectiveness

**Behavioral change estimate:** [X]% of this meeting will drive changed actions
- **Decision yield:** [Assessment if relevant — were decisions made relative to time spent?]
- **Data readiness:** [Assessment if relevant — was blocking information missing?]
- **Circular discussion:** [Assessment if relevant — topics revisited without new info?]
- **Intent vs. words:** [Assessment if relevant — signs of unstated concerns?] (Confidence: high/medium/low)

[Omit dimensions with insufficient evidence]

## Decision Making
[CONTENT-DEPENDENT: Include only if buying process was discussed]

- **Decision maker(s):** [Name, Role — what they care about]
- **Influencers:** [Name, Role — their stake]
- **Process:** [Approvals needed, procurement, timeline]
- **Competition:** [Who else they're talking to, how we compare]

## Budget Signals
[CONTENT-DEPENDENT: Include only if budget/pricing discussed]

- [Signal] → [Interpretation]
- **Range:** [Explicit or inferred]
- **Budget owner:** [Who controls the money]

## Objections
[CONTENT-DEPENDENT: Include only if concerns were raised]

- [Concern] — Severity: High/Med/Low — Our response: [How addressed] — Resolved: Yes/Partially/No

**Unspoken concerns:** [What they might worry about but didn't say] (Confidence: high/medium/low)

## Prospect Sentiment
[CONTENT-DEPENDENT: Include only if clear sentiment signals detected]

- **Enthusiasm:** High / Moderate / Low / Mixed — Evidence: [signals]
- **Pricing reaction:** Comfortable / Cautious / Concerned / Not discussed
- **Confidence in Nimble:** High / Building / Skeptical / Unclear
- **Urgency:** Urgent / Normal / Low priority — Evidence: [timeline pressure, competing priorities]
- **Momentum:** Gaining / Steady / Losing / Stalled

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

---

# Prospect Follow-Up

[Professional thank-you email format, ~150-200 words]

**Subject:** Following up on our conversation — {{COMPANY_NAME}} + Nimble

Hi [Name],

Thank you for taking the time to meet with us today. [1-2 sentences acknowledging what was discussed and showing you listened]

**Key points we covered:**
- [Point 1]
- [Point 2]
- [Point 3]

**Next steps:**
- [Our commitment with timeline]
- [Their expected action if discussed]

[Closing that matches the meeting tone — warm if warm, professional if formal]

Best regards,
[Your name]
```

## Transcript

[PASTE TRANSCRIPT HERE]
