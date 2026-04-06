# Meeting Analysis Templates Refinement

## Overview

### Problem Statement

The current meeting analysis templates are too long and rigid, leading to repetitive output and burying essential insights in verbose structure. Users need concise, actionable meeting intelligence without sacrificing valuable insights. Additionally, there's no template suitable for sharing directly with clients after meetings.

### Goals

1. **Reduce template verbosity** by 40-50% while preserving essential insights
2. **Introduce tiered sections** (required vs. content-dependent) to reduce rigidity
3. **Add a client-shareable output** to the client meeting template for professional post-meeting summaries
4. **Add meeting effectiveness assessment** to internal templates based on behavioral change principles
5. **Create a follow-up format** for sales meetings to support prospect communication
6. **Enable personal performance tracking** through optional self-assessment in analysis output

### Scope

**In scope:**
- Sales meeting analysis template
- Client meeting analysis template
- General/other meeting template
- New client-shareable summary output (dual-output from client template)
- New sales follow-up output (dual-output from sales template)

**Out of scope:**
- Interview analysis template (migrating to another system)
- Prototype scope template (no changes requested)

## User Stories

### Template Refinement
- As a Nimble team member, I want meeting analysis output that's half the current length so I can quickly extract key insights without wading through repetitive sections.
- As a Nimble team member, I want templates that only include relevant sections based on what was actually discussed so the output feels tailored rather than boilerplate.

### Client-Shareable Summary
- As a Nimble consultant, I want to generate a professional meeting summary I can email directly to clients after every project meeting so they have a clear record of decisions and next steps.
- As a Nimble consultant, I want both internal notes and a client-shareable summary from a single template run so I don't have to process the transcript twice.

### Sales Follow-Up
- As a Nimble sales team member, I want a polished follow-up email format generated alongside my sales analysis so I can quickly send a professional thank-you with key points.

### Meeting Effectiveness
- As a Nimble team member, I want to understand whether a meeting actually changed what people will do next, not just what they discussed, so I can identify meetings that waste time vs. drive progress.

### Advanced Signal Detection
- As a Nimble team member, I want the analysis to surface non-obvious signals (hedging patterns, question quality, convergence speed) so I can catch issues that surface-level summaries miss.
- As a Nimble team member, I want to know when commitments are vague or lack accountability so I can clarify before the meeting ends or follow up immediately.

### Personal Performance Tracking
- As a Nimble team member, I want to see an analysis of my own contribution when I participated in a meeting so I can track my effectiveness over time.
- As a Nimble team member, I want a consistent, compact format for my self-assessment so I can easily compare my performance across meetings.

## Business Rules

### Scope of Analysis: Single-Meeting Observations

**Important clarification:** This spec covers per-meeting analysis — what happened in THIS meeting and what should be done next. The analysis surfaces signals and observations from individual meetings, not diagnoses or assessments that require longitudinal data.

Some signals (e.g., psychological safety indicators, participation patterns) become meaningful only when tracked across multiple meetings. A single observation is a data point, not a conclusion:
- One person being quiet in one meeting ≠ psychological safety problem (they may be new, tired, or lack relevant input)
- One rapid convergence ≠ groupthink (the answer may have been obvious)
- One dominant speaker ≠ problematic pattern (they may have been the subject matter expert)

Templates should frame observations appropriately:
- Use "In this meeting..." not "This team has..."
- Use "may indicate" not "shows"
- Note when patterns would need confirmation across meetings

Team performance analytics (tracking patterns across meetings) is a separate capability outside this app's scope.

### Tiered Section System

Templates must use a two-tier section system:

| Tier | Behavior | Rationale |
|------|----------|-----------|
| **Required** | Always included in output | Core information that's always valuable |
| **Content-dependent** | Include only if transcript contains relevant discussion | Reduces noise and repetition |

The LLM decides which content-dependent sections to include based on transcript analysis. Users do not need to provide upfront context.

### Dual-Output Structure

**Client Meeting Template:**
```
## Internal Analysis
[Full notes with effectiveness assessment, sentiment, private observations]

## Client-Shareable Summary
[Polished, concise: Summary → Decisions → Action Items → Next Steps]
```

**Sales Meeting Template:**
```
## Sales Intelligence
[Full analysis with deal signals, competitive info, strategy]

## Prospect Follow-Up
[Thank-you format with key discussion points and next steps]
```

### Output Length Guidelines

| Template | Target Length | Notes |
|----------|---------------|-------|
| Sales - Intelligence | ~400-500 words | Focus on actionable insights |
| Sales - Follow-up | ~150-200 words | Brief, professional email format |
| Client - Internal | ~400-500 words | Comprehensive but scannable |
| Client - Shareable | ~200-300 words | Executive summary style |
| Other/General | ~300-400 words | Flexible based on meeting complexity |

### Meeting Effectiveness Assessment

Include in internal-facing outputs only. Assess meetings against four principles, anchored by one meta-principle:

**Meta-principle:** A meeting is effective when it changes what people will do next — not just what they think. The analysis should estimate what percentage of the meeting will actually drive changed behavior.

**Four Assessment Dimensions:**

1. **Decision yield vs. airtime**
   - How many resolved decisions came out relative to total time spent?
   - A high-performing meeting front-loads decisions and uses remaining time to stress-test them, not discover them.
   - Flag: Low yield = lots of discussion, few concrete outcomes.

2. **Data readiness**
   - Were the right inputs available before the meeting started?
   - Identify discussion that was structurally unresolvable because blocking information wasn't in the room.
   - Flag: Meeting convened before a critical input was available.

3. **Circular discussion rate**
   - How many times did the group revisit a point that had already reached a conclusion?
   - Once is healthy (someone caught something). Twice suggests the conclusion wasn't clean. Three+ times indicates a facilitation problem or unresolved interpersonal dynamic.
   - Flag: Topics revisited 3+ times without new information.

4. **Intent vs. words**
   - When someone raises a concern multiple times in different language, the stated concern probably isn't the real one.
   - When someone shuts down hypotheticals but keeps generating them, there's anxiety underneath worth surfacing.
   - Meetings that only operate at face value miss what's actually blocking progress.
   - Flag: Patterns suggesting unstated concerns or blockers.

**Output format:** Brief "Meeting Effectiveness" section with:
- Overall effectiveness estimate (percentage of meeting that will change behavior)
- 1-2 sentence assessment for each dimension that showed signal
- Omit dimensions where there's insufficient evidence

### Contribution Quality Analysis

Include in internal-facing outputs only. Assesses individual contributions beyond surface-level participation metrics.

**Anti-pattern: Volume ≠ Value**

LLMs tend to equate airtime with importance. The templates must explicitly instruct the LLM to distinguish between:
- **Airtime** — How much someone spoke
- **Signal** — How much of what they said moved the conversation forward

Someone speaking loudly, frequently, or over others may actually be:
- Going in circles (repeating the same point without new information)
- Asserting rather than persuading (stating positions without building cases)
- Filling silence rather than adding value
- Dominating without leading (controlling airtime without driving outcomes)

**What to assess:**

1. **Progress drivers**
   - Who introduced ideas that were adopted?
   - Who asked questions that unlocked stuck discussions?
   - Who synthesized disparate points into actionable conclusions?
   - Note: This person may have spoken very little.

2. **Airtime vs. impact ratio**
   - Flag participants with high airtime but low decision influence
   - Highlight participants with low airtime but high impact (the quiet person whose single question changed the direction)
   - **40% threshold**: Flag any speaker who consumed more than 40% of talk-time (research-backed threshold for healthy meetings)

3. **Rhetorical patterns**
   - Distinguish building a case (evidence → reasoning → conclusion) from assertion (repeating a position louder)
   - Note when someone "wins" through persistence rather than persuasion
   - Identify when volume or interruption substitutes for substance

4. **Listening signals**
   - Did participants build on others' points, or just wait for their turn?
   - Were questions asked to understand, or to set up a rebuttal?
   - Did anyone explicitly change their position based on discussion?

**Output format:** Brief "Contribution Dynamics" section (content-dependent — include only if notable patterns detected):
- Who drove progress (with evidence)
- Airtime/impact mismatches worth noting
- Patterns that may be affecting meeting effectiveness

**Guidance for LLM:** Do not assume the person who spoke most was most valuable. Do not assume confident or loud statements are correct or important. Assess based on what actually moved the meeting toward outcomes.

### Additional Signal Detection

Include in internal-facing outputs only. These are content-dependent sections — include only when notable signals are detected.

**1. Question Quality Analysis**

Research shows question quality matters more than quantity (Gong: winners ask 15-16 questions vs. 20 for losers — interrogation-style backfires).

Assess:
- **Question types**: Clarifying (seeking understanding) vs. challenging (testing assumptions) vs. leading (steering toward predetermined answer)
- **Question distribution**: Who asks questions vs. who only makes statements?
- **Question response**: Were questions actually answered, or deflected?

Flag:
- Meetings with very few questions (passive acceptance risk)
- Interrogation patterns (rapid-fire questions without listening to answers)
- Important questions that went unanswered

**2. Hedging Language Detection**

Hedging words (might, could, perhaps, sort of, kind of, I think, it seems) indicate uncertainty, lack of commitment, or political positioning.

Assess:
- Who hedges frequently, and in what contexts?
- Is hedging concentrated when disagreeing with specific people?
- Does hedging correlate with topics that later surface as unresolved?

Flag:
- High hedging frequency from specific participants
- Hedging patterns that suggest deferred disagreement rather than genuine uncertainty
- Commitments made with heavy hedging ("I think we could probably try to...")

**3. Convergence Quality Check**

Research on hidden profiles shows groups often converge too quickly, missing unique information held by individuals. Rapid agreement without dissent is a warning sign.

Assess:
- Did the group explore alternatives before converging?
- Was dissent expressed, or did everyone quickly align?
- Did anyone with relevant expertise stay silent?

Flag:
- Rapid convergence without expressed dissent (groupthink risk)
- Early preference anchoring (senior person states position, others fall in line)
- Unique perspectives that went unexplored

**4. Commitment Strength Assessment**

44% of meeting action items are never completed. Vague commitments are a leading cause.

Assess commitment clarity on a spectrum:
- **Strong**: "I will deliver X by Friday" (clear verb, owner, deadline)
- **Moderate**: "I'll look into that this week" (owner, rough timeline, vague deliverable)
- **Weak**: "We should explore this" (no owner, no timeline)
- **Empty**: "Someone needs to handle that" (diffusion of responsibility)

Flag:
- Commitments without clear owners
- Commitments without deadlines
- "We" commitments with no individual accountability
- High ratio of weak/empty commitments to strong ones

**5. Topic Drift Detection**

Track when conversation wanders from stated agenda or goals.

Assess:
- Did discussion stay focused on the meeting's purpose?
- Were tangents productive (uncovered important issues) or wasteful?
- Who brought the conversation back on track?

Flag:
- Significant time spent on topics unrelated to meeting purpose
- Repeated drift to the same off-topic issue (may indicate an unaddressed concern)
- Meetings that never addressed their stated agenda

**Output format:** Include relevant signals in a "Meeting Signals" section, grouped by category. Only include categories where notable patterns were detected.

### Personal Performance Self-Assessment (Optional)

An optional section that analyzes the user's own contribution when they participated in the meeting. Enables longitudinal self-improvement tracking.

**Activation flow:**

The template should include an explicit opt-in prompt at the start:

```
Before analyzing, I have a question:

Would you like me to include a personal performance analysis of your own
contribution to this meeting? This section analyzes your talk time, question
quality, hedging patterns, and other behaviors to support self-improvement
tracking over time.

[ ] Yes, include my performance analysis
[ ] No, skip this section

If yes: What name or speaker label identifies you in the transcript?
[Your name]: _______
```

Only include the self-assessment section if the user explicitly opts in AND provides their identifier. Otherwise, omit it entirely.

**What to assess:**

1. **Contribution metrics**
   - Talk time percentage (approximate from transcript segment count)
   - Questions asked (count and types: clarifying / challenging / leading)
   - Ideas adopted (contributions that became decisions or action items)
   - Progress driver identification (did they move things forward?)

2. **Behavioral observations**
   - Hedging instances (flagged hedging language from this speaker)
   - Interruption patterns (interrupted others / was interrupted)
   - Building vs. competing (referenced others' ideas or only pushed own)
   - Commitment clarity (strong / moderate / vague commitments made)

3. **Quality indicators**
   - Listening signals (built on others' points, or waited to speak?)
   - Position flexibility (changed view based on discussion?)
   - Directness (said what they thought, or hedged around it?)

4. **Patterns to watch**
   - Any concerning patterns specific to this person's participation
   - Behaviors that may be worth tracking across meetings

**Output format:**

```markdown
## Your Contribution ([Speaker Name])

### Metrics
- Talk time: ~XX%
- Questions asked: X (X clarifying, X challenging, X leading)
- Ideas adopted: X
- Progress driver: Yes/No — [brief evidence if yes]

### Observations
- **Hedging:** [None detected / X instances — context]
- **Interruptions:** [Interrupted others X times / Was interrupted X times]
- **Commitments:** [Strong/Moderate/Vague] — [examples]
- **Listening:** [Built on others' points / Primarily advanced own ideas]

### Patterns to Watch
- [Specific observation relevant to self-improvement]
- [Another observation if applicable]

### Trackable Summary
`XX% talk | XQ | X adopted | driver:[y/n] | hedge:X | commits:[s/m/v]`
```

**The Trackable Summary line** provides a consistent, compact format for longitudinal tracking. Users can copy this line to a personal tracking system (e.g., Obsidian) to compare across meetings over time.

**Guidance for analysis:**

- Be direct and honest — the purpose is self-improvement, not ego protection
- Focus on observable behaviors, not personality judgments
- Frame observations constructively (what to watch, not what's wrong)
- Apply the same "volume ≠ value" principle — high talk time isn't automatically good or bad
- Note both strengths and areas for growth

### Potential Issues Detection

Include in internal-facing outputs only. A dedicated section that surfaces risks which could derail progress if left unaddressed.

**Categories to identify:**

1. **Confusions**
   - Moments where participants appeared to be talking past each other
   - Terms or concepts used differently by different people
   - Answers that didn't address the actual question asked

2. **Misunderstandings**
   - Apparent agreement that may be based on different interpretations
   - Assumptions one party made that another party may not share
   - Technical or domain terms that may have been misinterpreted

3. **Hidden disagreements**
   - Surface agreement with signals of underlying resistance (hedging language, qualified yeses, body language cues if noted)
   - Topics where someone conceded quickly but may not actually be aligned
   - Patterns of "agreeing to disagree" without explicit acknowledgment

4. **Unresolved items**
   - Decisions that were discussed but never explicitly closed
   - Questions raised but not answered
   - Items deferred without a clear plan to revisit
   - Ambiguous outcomes ("we'll figure it out" without specifics)

**Output format:** "Potential Issues" section listing items with:
- Category label (Confusion / Misunderstanding / Hidden Disagreement / Unresolved)
- Brief description of the issue
- Evidence from the transcript (quote or paraphrase)
- Suggested follow-up action where applicable

Omit this section entirely if no potential issues were detected.

### Format Requirements

- Use markdown with minimal tables (prefer bullets and sections)
- Tables only for structured data that genuinely benefits from tabular format
- Output must be readable in email, Slack, and markdown renderers

## Data Requirements

### Template Metadata

Each template file must include:
- Template name and purpose
- Target output sections (required vs. content-dependent)
- Target length guidance
- Dual-output specification (if applicable)

### API Integration

The existing `TEMPLATE_FILES` mapping in `backend/routers/analysis.py` must be updated:
- No new template types needed (client-shareable is part of client template)
- Template content changes only; API structure unchanged

### Existing Templates to Modify

| File | Changes |
|------|---------|
| `templates/sales_meeting_analysis.md` | Condense sections, add tiered system, add follow-up output, add effectiveness assessment |
| `templates/client_meeting_analysis.md` | Condense sections, add tiered system, add client-shareable output, add effectiveness assessment |
| `templates/other.md` | Condense sections, add tiered system, add effectiveness assessment |

## Edge Cases

### Insufficient Transcript Content

**Scenario:** Transcript is too short or lacks substantive discussion for meaningful analysis.

**Expected behavior:** LLM should:
1. Still produce required sections with available information
2. Explicitly note "Insufficient signal" for content-dependent sections rather than fabricating content
3. Note in Meeting Effectiveness assessment that there's insufficient content to evaluate behavioral change potential

### Mixed-Language Transcripts

**Scenario:** Meeting transcript contains Thai, English, or mixed content.

**Expected behavior:** Output should always be in English regardless of transcript language (existing behavior, maintain it).

### No Decisions Made

**Scenario:** Meeting was purely discussion with no explicit decisions.

**Expected behavior:**
- Decisions section should state "No explicit decisions made"
- Effectiveness assessment should flag low decision yield vs. airtime
- Client-shareable version should omit Decisions section entirely rather than showing "none"

### Client-Shareable Content Safety

**Scenario:** Internal analysis contains sensitive observations that shouldn't appear in client output.

**Expected behavior:** Client-shareable output must never include:
- Client sentiment analysis
- Private/internal observations
- Competitive or budget intelligence
- Risk assessments about the client relationship
- Potential Issues section (confusions, hidden disagreements, etc.)
- Meeting Effectiveness assessment
- Anything from a "Private Notes" equivalent section

### Missing Action Item Details

**Scenario:** Action items discussed but owners or deadlines not specified.

**Expected behavior:**
- List action items with "Owner: TBD" or "Deadline: TBD" rather than omitting
- Effectiveness assessment should note this impacts decision yield (decisions without clear ownership are less likely to change behavior)
- Client-shareable version should still include the action item with TBD markers

### Potential Issues Confidence

**Scenario:** LLM detects a possible hidden disagreement or misunderstanding but isn't certain.

**Expected behavior:**
- Include the observation with explicit uncertainty language ("may indicate," "possibly," "worth checking")
- Provide the evidence that triggered the observation so the user can judge
- Err on the side of surfacing potential issues rather than suppressing uncertain ones — a false positive is less costly than missing a real problem

### Transcript-Only Limitations

**Scenario:** Analysis requires interpreting tone, emotion, or non-verbal cues that aren't present in the transcript.

**Expected behavior:**
- Acknowledge when an assessment is limited by text-only analysis (e.g., "Based on word choice alone, this appears to be agreement, but tone could indicate otherwise")
- Focus on linguistic signals available in text: word choice, hedging language, repetition patterns, question types, response lengths
- Do not fabricate emotional interpretations — if the transcript doesn't support a reading, note insufficient signal
- Flag moments where audio context would materially change the interpretation (e.g., "The phrase 'that's fine' appears 3 times from Speaker B — tone would clarify if this is genuine agreement")

### Self-Assessment Speaker Not Found

**Scenario:** User opts into self-assessment and provides a name, but that name doesn't match any speaker in the transcript.

**Expected behavior:**
- Inform the user that the name wasn't found in the transcript
- List the speaker names/labels that ARE in the transcript
- Ask the user to clarify which speaker they are
- Do not guess or assume — wait for user confirmation

### Self-Assessment Insufficient Data

**Scenario:** User's identified speaker has very few segments in the transcript (e.g., spoke only 2-3 times).

**Expected behavior:**
- Still produce the self-assessment section
- Note that limited data affects assessment accuracy
- Focus on what CAN be observed from available segments
- Omit metrics that require more data (e.g., "Talk time: ~5% — insufficient segments for detailed behavioral analysis")

## Open Questions

### For Engineering

1. **Template versioning**: Should we version templates (e.g., `v2` suffix) during transition, or replace in-place? Users may have muscle memory with current output structure.

2. **Output length enforcement**: The LLM may not reliably hit length targets. Should the prompt include explicit word count guidance, or rely on structural guidance alone?

3. **Interpretive confidence calibration**: Both "intent vs. words" and "Potential Issues" require nuanced interpretation. The edge case says to err toward surfacing issues, but should the template also instruct the LLM to rate its confidence level for each observation?

### For Product

1. **Template selection UX**: With dual-output templates, should the frontend explain that client template now includes shareable output, or is the template description sufficient?

2. **Feedback loop**: How will we know if the refined templates are working better? Should we add a simple thumbs-up/down on analysis output?

## Related Specifications

### Audio-Based Emotional Intelligence

A separate spec (`docs/specs/audio-emotional-intelligence.md`) covers extracting emotional and prosodic features from audio recordings. This would significantly enhance the analysis capabilities defined in this spec by adding:
- Emotional tone detection (frustration, confidence, uncertainty)
- Prosodic analysis (volume patterns, pace, pitch)
- Interaction patterns (interruptions, talking over)
- Word-tone mismatches ("That's fine" said with frustration)

The current spec's transcript-only analysis is limited to linguistic signals. Audio analysis would unlock a critical dimension that's currently lost.
