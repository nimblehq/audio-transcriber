---
description: Run a code review on the current branch
---

You are now running an **Argus code review** on the current branch.

## Instructions

1. Remember the current branch: !`git branch --show-current`
2. Review the diff provided by `git diff develop...HEAD` to understand what was implemented
3. Use the architect agent via Task to review the diff, but the architect should return the review summary as text (no handoff document needed)
4. Report the review summary to the user

## Constraints

- Do NOT fix any issues or files which are unrelated to the diff
- Do NOT amend existing commits; always create new commits for fixes
- Do NOT write a handoff document, because there is no next agent to hand off to
