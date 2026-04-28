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

### Phase 6: Spec Drift Check

## Spec Drift Check

After implementation is complete and the architect review passes, check whether the implementation drifts from the spec. Skip this step entirely if `{{config.workflow.drift_detection}}` is `false`.

### When to Run

- Run **after** implementation and architect review
- Run **before** PR creation
- Only check specs with `status: implemented` in their YAML frontmatter
- If no matching spec exists for this story, skip the drift check silently

### How to Find the Matching Spec

1. Extract the story ID from the branch name (e.g., `feature/sc-42-...` → `sc-42`)
2. Search `docs/specs/*.md` for files with YAML frontmatter containing a `story_ids` array that includes this story ID
3. Only consider specs where `status: implemented`
4. If no spec has a matching `status` or `story_ids`, skip the check

### How to Perform the Check

1. Read the matching spec file(s)
2. Read the persisted plan from `docs/plans/` (if it exists)
3. Get the PR diff with `git diff develop...HEAD`
4. Compare the spec + plan + diff and classify each discrepancy:

**Expected drift** — the plan's "Deviations from Spec" section documents this change:
- Auto-update the spec to reflect the implementation
- Commit the spec update on the current branch with message: `[drift-check] Update spec to match implementation`

**Unexpected drift** — the implementation contradicts the spec and the plan does not mention it:
- Report as a warning to the user; do NOT auto-fix
- Include the spec excerpt and the contradicting code

**Business rule violation** — a business rule (BR-XXX) is contradicted, even if the plan mentions it:
- Always flag as a warning, never auto-fix
- Business rules require explicit human approval to change

### Conservative Mode

If no persisted plan exists in `docs/plans/`, treat ALL drift as unexpected:
- Flag every discrepancy as a warning
- Do not auto-fix anything
- Inform the user that conservative mode is active because no plan was found

### After the Check

- Update the spec's `last_verified` frontmatter field to today's date (YYYY-MM-DD)
- Commit the frontmatter update alongside any spec content changes
- If there are unexpected drift warnings, present them to the user before proceeding to PR creation
- The user may choose to:
  - Fix the code to match the spec
  - Update the spec manually
  - Acknowledge the drift and proceed anyway


### Phase 7: QA Verification

18. Create the PR following the "Create PR Guidelines" below
19. Use the quality-assurance agent via Task to verify each AC and truth
20. Address any failures and re-verify

## Create PR Guidelines

> **Reminder**: Read tool uses `file_path` (not `file`). Bash tool uses `command` (not `cmd`).

When creating the PR, follow these guidelines:

1. Check if `.github/PULL_REQUEST_TEMPLATE.md` exists in the project root
   - If the template DOES exist:
      1. Read the template file, and populate each section using context from the ticket and commits
      2. Populate the `Story:` field based on the PM tool:
         - **Shortcut**: `[{{config.commit_prefix}}-{id}](https://app.shortcut.com/{org}/story/{id})`
         - **Linear**: `[{{config.commit_prefix}}-{id}](https://linear.app/{workspace}/issue/{id})`
         - **GitHub Projects** / **GitHub Issues**: `[#{number}](https://github.com/{owner}/{repo}/issues/{number})` — resolve `{owner}/{repo}` from `config.github_repo` if set, otherwise auto-detect from `git remote get-url origin`
      3. Use the filled template as the body upon creating the PR
   - If the template DOES NOT exist, stop and warn the user
2. Push the branch to remote with the `git push -u origin HEAD` command
3. Determine the title based on the ticket title, following the `[<prefix>-<ticket id>] <ticket title>` format
4. Determine the label based on the ticket type:
   - story → `type : feature`
   - bug → `type : bug`
   - chore → `type : chore`
5. Create the PR using the GitHub CLI: `gh pr create --draft --base develop --assignee @me --label "<label>" --title "<title>" --body "<body>"`


## Constraints

- Do NOT write code before the user approves the implementation plan
- Do NOT skip the architect review
- Do NOT open a PR before the architect review passes
- Commit progress frequently with atomic commits
