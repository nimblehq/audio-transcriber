---
description: Run architect review on the current branch
---

You are now running an **Argus architect review** on the current branch.

## Instructions

1. Determine the current branch: !`git branch --show-current`
2. Get the diff against the base branch: !`git diff develop...HEAD --stat`
3. Use the architect agent via Task to review all changed files against the four convention layers:
   - **Layer 1A**: Stack-agnostic best practices
   - **Layer 1B**: Stack-specific best practices
   - **Layer 2**: Codebase patterns (`.argus/codebase/CONVENTIONS.md`)
   - **Layer 3**: Team conventions
   - **Layer 4**: Project overrides (`.argus/conventions.md`)
4. For Critical and Major issues: fix directly on the branch
5. For Minor issues: fix if unambiguous, comment otherwise
6. For Nit issues: comment only
7. Report the review summary to the user

## Context

- Current branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -10`
