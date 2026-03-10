# Prototype Scope Template

## Overview

### Problem

After sales or client meetings, Nimble's team builds rapid prototypes using AI coding tools (Replit Agent, Lovable, Bolt) to demonstrate what a solution could look like. Today, translating a meeting conversation into a well-structured prompt for these tools is manual and inconsistent. Key details from the conversation — client terminology, product names, priorities, visual references — are often lost or forgotten.

### Goals

- Generate a structured, AI-coding-tool-optimized document from a meeting transcript that can be directly pasted into Replit Agent (or similar) to produce a prototype
- Extract real content from the conversation (client's products, branding, terminology) so the prototype feels tailored, not generic
- Reflect the client's stated priorities so the prototype focuses on what matters most to them

### Scope

Add a new "Prototype Scope" template to the existing analysis template system. No changes to the analysis workflow, UI patterns, or backend architecture.

## User Stories

- As a user, I can select "Prototype Scope" from the analysis template dropdown so that I can generate a prototype-ready prompt from any meeting transcript
- As a user, I get a structured document that I can paste directly into Replit Agent or a similar AI coding tool to build a prototype
- As a user, the generated prompt extracts real content from the conversation (product names, branding, client terminology) so the prototype feels personalized
- As a user, the generated prompt reflects priorities discussed in the meeting so the prototype focuses on what the client cares about most

## Business Rules

| ID | Rule | Rationale |
|----|------|-----------|
| BR-1 | The template must be available regardless of meeting type (sales, client, interview, other) | Prototype scoping can follow any type of meeting |
| BR-2 | The generated output must be structured in build phases (foundation, core feature, polish) | AI coding tools produce better results with iterative, phased prompts rather than monolithic ones |
| BR-3 | The output must instruct the LLM to extract real content from the transcript (product names, pricing, categories, brand language) rather than using placeholder text | Prototypes with targeted content are significantly more impactful to clients |
| BR-4 | The output must instruct the LLM to identify and prioritize features based on what the client emphasized or described as high priority | The prototype should demonstrate what the client cares about, not what's easiest to build |
| BR-5 | The output must include explicit non-goals/out-of-scope items | AI coding tools cannot infer boundaries from omission and will add unnecessary features otherwise |

## Data Requirements

### New Template File

A new markdown template file (`templates/prototype_scope.md`) containing the LLM prompt. The prompt instructs the LLM to analyze the transcript and produce output with these sections:

1. **Project Overview** — App name (derived from client's product/service), one-line description, target user, core problem
2. **Brand & Visual Direction** — Colors, visual style, reference sites/competitors mentioned in the call
3. **Pages & Navigation** — Each page with purpose and key components, navigation structure
4. **Core Features** (max 5-7, prioritized) — Feature name, description, acceptance criteria, using the client's terminology
5. **Sample Data & Content** — Real product/service names, categories, pricing, descriptions, and workflows extracted from the conversation
6. **User Flows** (2-3 primary journeys) — Step-by-step with page references
7. **Non-Goals / Out of Scope** — What the prototype does NOT include (e.g., real auth, payment processing, backend APIs)
8. **Build Phases** — Phase 1: Foundation (layout, nav, branding, landing page), Phase 2: Primary feature with sample data, Phase 3: Secondary features and polish. Each phase self-contained enough to be used as a single prompt

### Backend Wiring

- Add entry to `TEMPLATE_FILES` dict in `backend/routers/analysis.py`
- Template key: `"prototype"`

### Frontend Wiring

- Add `<option value="prototype">Prototype Scope</option>` to the template dropdown in `frontend/js/components/analysis-viewer.js`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Meeting transcript has no clear product/feature discussion | The LLM should note that insufficient detail was found and list what additional information is needed |
| Client mentioned many features with no clear prioritization | The LLM should infer priority from conversation signals (time spent discussing, enthusiasm, "must-have" language) and state its reasoning |
| Conversation is in Thai or mixed English/Thai | The generated prototype scope should be in English regardless of transcript language |
| Very short transcript (few segments) | The LLM should produce what it can and explicitly flag gaps |

## Open Questions

| ID | Question | Impact |
|----|----------|--------|
| OQ-1 | Should the template output be in a specific markdown format that works best with Replit's "Improve Prompt" feature, or is plain structured markdown sufficient? | May affect template wording |
| OQ-2 | Should the build phases include estimated complexity hints (e.g., "this phase should take ~1 prompt iteration")? | Useful for less experienced prototype builders but may be misleading |
