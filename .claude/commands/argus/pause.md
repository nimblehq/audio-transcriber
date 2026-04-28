---
description: Save session context for later resumption
---

You are now running **Argus pause**. Save the current session context so it can be resumed later.

## Instructions

1. Analyze the current conversation to identify:
   - What task/story is being worked on
   - What has been completed so far
   - What remains to be done
   - Any open questions or blockers
   - Current branch and uncommitted changes
2. Commit any uncommitted progress with an appropriate message
3. Write the session context to `.argus/continue-here.md`:

```markdown
# Continue Here

## Task
[Story ID and title, or task description]

## Completed
[What was done in this session]

## Remaining
[What still needs to be done]

## Current State
- Branch: [current branch]
- Last commit: [commit hash and message]
- Uncommitted changes: [yes/no, what]

## Open Questions
[Any blockers or decisions needed]

## Context
[Key findings, decisions made, or important context for resumption]
```

4. Confirm to the user that the session has been saved
