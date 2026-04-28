---
description: Full planning pipeline from feature idea to backlog stories
argument-hint: "[feature idea or path to PRD]"
---

You are now running the **full Argus planning pipeline**. This orchestrates the Business Analyst and Product Manager agents in sequence with confirmation gates between steps.

The user's input is: **$ARGUMENTS**

## Pipeline

### Step 1: Discovery and Spec (Business Analyst)

1. Read `.argus/project.md` for project context
2. Read `.argus/codebase/ARCHITECTURE.md` and `.argus/codebase/INTEGRATIONS.md` if they exist
3. Interview the user to understand the feature:
   - Ask clarifying questions (3-5 per round)
   - Surface gaps, challenge assumptions, identify edge cases
4. If domain research is needed, use the product-researcher agent via Task
5. Write the spec document to `docs/specs/{feature-name}.md`

**CONFIRMATION GATE**: Present the spec to the user. Wait for explicit approval before proceeding. If the user requests changes, revise and re-present.

### Step 2: Story Breakdown (Product Manager)

6. Read the approved spec
7. Break into vertical-slice user stories with AC, truths, business rules, dependencies, and sizing
8. Reject horizontal slices

**CONFIRMATION GATE**: Present the story breakdown to the user. Wait for explicit approval before creating stories in the PM tool.

### Step 3: Story Creation

9. Create approved stories in the PM tool
10. Confirm creation with story IDs and links

## Rules

- Never skip a confirmation gate
- Never proceed to Step 2 without an approved spec
- Never create stories without user approval of the breakdown
- If the user wants to stop after Step 1, that is fine
