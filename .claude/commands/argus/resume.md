---
description: Restore session context from a previous pause
---

You are now running **Argus resume**. Restore the context from a previously paused session.

## Instructions

1. Read `.argus/continue-here.md`
   - If it doesn't exist, inform the user that no paused session was found
2. Present a summary of the saved context:
   - What task was being worked on
   - What was completed
   - What remains
   - Any open questions
3. Verify the current state matches expectations:
   - Check the current branch: !`git branch --show-current`
   - Check for uncommitted changes: !`git status --short`
   - Verify the last commit matches: !`git log --oneline -1`
4. If there are discrepancies, flag them to the user
5. Ask the user if they want to continue from where they left off
6. Once confirmed, proceed with the remaining work
