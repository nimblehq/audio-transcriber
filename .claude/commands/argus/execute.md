---
description: Pick up a story and implement it through the full execution pipeline
argument-hint: "[story ID or URL]"
---

You are now running the **Argus execution pipeline** using the Software Engineer agent workflow.

The user's input is: **$ARGUMENTS**

## Instructions

### Phase 1: Story Analysis

1. Read the story from the PM tool using the story ID or URL provided
2. Load the story's AC, truths, business rules, and technical considerations
3. Read the spec file referenced in the story
4. Read `.argus/codebase/STRUCTURE.md` and `.argus/codebase/CONVENTIONS.md` if they exist
5. Load `.argus/guardrails.md` if it exists to avoid known dead ends

### Phase 2: Technical Research

6. If there are technical unknowns (libraries, patterns, approaches), use the technical-researcher agent via Task to investigate
7. Review research findings before proceeding

### Phase 3: Implementation Plan

8. Present an implementation plan to the user for approval:
   - Files to create or modify
   - Approach for each AC
   - Commit sequence
   - TDD or standard mode choice with rationale
   - Risks, trade-offs, or open questions
9. **Wait for user approval before writing any code**

## Plan Persistence

After the user approves the implementation plan, persist it to `docs/plans/` before writing any code:

1. Create the `docs/plans/` directory if it does not exist
2. Save the plan to `docs/plans/{story-id}-{story-name-slug}.md` (e.g., `docs/plans/sc-42-user-authentication.md`)
   - Slugify the story name: lowercase, replace spaces and special characters with hyphens, remove consecutive hyphens
3. Use the following structure:

```markdown
# Plan: {Story Title}

**Story**: {story-id}
**Spec**: {path to spec file, or "N/A" if no spec exists}
**Branch**: {branch-name}
**Date**: {YYYY-MM-DD}
**Mode**: {TDD | Standard} — {one-line rationale}

## Technical Decisions

### TD-1: {Decision title}
- **Context**: {Why this decision was needed}
- **Decision**: {What was chosen}
- **Alternatives considered**: {What else was evaluated}

## Files to Create or Modify

- `path/to/file.ts` — {what and why}

## Approach per AC

### AC 1: {AC text}
{Implementation approach}

## Commit Sequence

1. {Commit description}

## Risks and Trade-offs

- {Risk or trade-off}

## Deviations from Spec

- {Intentional difference from spec, with rationale. Section omitted if no spec exists.}

## Deviations from Plan

_Populated after implementation._

- {What changed from the plan, with rationale}
```

4. If no spec exists for the story, omit the "Deviations from Spec" section entirely
5. Populate "Deviations from Plan" after implementation with any changes from the original plan
6. Commit the plan file before starting implementation; update it with deviations before opening the PR


### Phase 4: Implementation

10. Create a feature branch following Gitflow (`feature/{story-branch-name}`)
11. Persist the approved plan following the plan persistence guidelines above
12. Implement against the approved plan
13. Write tests covering all AC and truths
14. Commit progress atomically with story ID prefix

### Phase 5: Architecture Review

15. Use the architect agent via Task to review the branch
16. Address any Critical or Major issues
17. Iterate until the review passes

### Phase 6: QA Verification

18. Open the PR targeting develop following the PR creation guidelines below
19. Use the quality-assurance agent via Task to verify each AC and truth
20. Address any failures and re-verify

## PR Creation

When opening a PR:

1. Check if `.github/PULL_REQUEST_TEMPLATE.md` exists in the project root
2. If a template exists:
   - Read the template file
   - Populate each section using context from the story, implementation plan, and commits
   - Use the filled template as the PR body
3. If no template exists, structure the PR body with:
   - A link to the story in the PM tool
   - A summary of what changed and why
   - Key changes as a bullet list
4. Create the PR with `gh pr create` targeting `develop`, passing the populated body via `--body`


## Constraints

- Do NOT write code before the user approves the implementation plan
- Do NOT skip the architect review
- Do NOT open a PR before the architect review passes
- Commit progress frequently with atomic commits
