---
description: Quick task — create a chore, implement it, and mark done
argument-hint: "[task description]"
---

You are now running an **Argus quick task**. This is a streamlined workflow for small chores that don't need full spec or story breakdown.

The user's input is: **$ARGUMENTS**

## Instructions

1. Create a chore in the PM tool with a concise title based on the user's description
2. Move the chore to "In Progress"
3. Create a feature branch following Gitflow (`chore/{branch-name}`)
4. Implement the task with atomic commits
5. Run tests to verify nothing is broken
6. Open a PR targeting develop following the PR creation guidelines below
7. Move the chore to "In QA"
8. Report completion to the user with the PR link and chore ID

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

- Keep it simple — quick tasks should not require multi-step planning
- Follow Gitflow and commit conventions
- If the task turns out to be complex, suggest switching to `/argus:execute` instead
