# Prototype Scope Template

Use this prompt with a meeting transcript to generate a structured prototype scope document that can be pasted directly into an AI coding tool (Replit Agent, Lovable, Bolt, etc.).

## Prompt

You are analyzing a meeting transcript to produce a **prototype scope document**. This document will be pasted directly into an AI coding tool to build a working prototype.

**Important instructions:**
- Extract **real content** from the transcript: product names, pricing, categories, brand language, terminology the client actually used. Do NOT use generic placeholders like "Product A" or "Lorem ipsum."
- Prioritize features based on what the client **emphasized** in the conversation — look for signals like time spent discussing, enthusiasm, "must-have" language, and repeated mentions.
- If the transcript is in Thai or mixed English/Thai, produce the output **entirely in English**.
- If the transcript lacks sufficient product or feature discussion, clearly state what information is missing and list what additional details are needed to produce a complete scope.

### Output Format

Produce the following sections in markdown:

```markdown
# [App/Product Name — derived from client's product or service]

> One-line description of what this prototype demonstrates.

**Target User:** [Who will use this — extracted from conversation]
**Core Problem:** [What problem this solves — in the client's own words where possible]

## Brand & Visual Direction

- **Colors:** [Any colors, palettes, or visual preferences mentioned]
- **Style:** [Modern, minimal, playful, corporate — based on conversation cues]
- **References:** [Any websites, competitors, or visual references the client mentioned]
- **Logo/Branding:** [Any brand assets or guidelines discussed]

## Pages & Navigation

| Page | Purpose | Key Components |
|------|---------|----------------|
| [Page name] | [What this page does] | [Main UI elements] |

**Navigation:** [Describe the navigation structure — sidebar, top nav, tabs, etc.]

## Core Features (prioritized)

> Ordered by client priority — features the client emphasized most are listed first.

### 1. [Feature Name — using client's terminology]
- **Description:** [What it does]
- **Why prioritized:** [What signals from the conversation indicate this matters most]
- **Key behaviors:** [Acceptance criteria in plain language]

### 2. [Feature Name]
...

(Maximum 5-7 features)

## Sample Data & Content

Use this real data extracted from the conversation to populate the prototype:

### [Category — e.g., Products, Services, Menu Items]
| Name | Description | Price/Details |
|------|-------------|---------------|
| [Real name from transcript] | [Real description] | [Real pricing if mentioned] |

### [Additional categories as needed]
...

## User Flows

### Flow 1: [Primary user journey name]
1. User lands on [page]
2. User [action] → sees [result]
3. ...

### Flow 2: [Secondary journey]
...

(2-3 primary flows)

## Non-Goals / Out of Scope

This prototype does NOT include:
- [e.g., Real authentication — use mock login]
- [e.g., Payment processing — show UI only, no real transactions]
- [e.g., Backend API — all data is hardcoded/mocked]
- [List items based on what was discussed as future work or explicitly excluded]

## Build Phases

### Phase 1: Foundation
> Layout, navigation, branding, and landing page.

Set up the app with:
- [App framework/structure based on pages listed above]
- Navigation: [structure from Pages section]
- Brand styling: [colors, fonts, style from Brand section]
- Landing/home page with [key elements]
- Use [real brand language and content from transcript]

### Phase 2: Core Feature + Sample Data
> Build the primary feature with real content.

Implement:
- [#1 priority feature from Core Features]
- Populate with sample data from the Sample Data section
- [Key user flow from User Flows]
- [Any secondary feature tightly coupled to the primary one]

### Phase 3: Secondary Features & Polish
> Remaining features and refinements.

Add:
- [Remaining features from Core Features list]
- [Secondary user flows]
- Responsive design adjustments
- Empty states and loading states
- [Any polish items mentioned in conversation]
```

## Transcript

[PASTE TRANSCRIPT HERE]
