---
description: Run QA verification on the current PR
argument-hint: "[story ID or PR URL]"
---

You are now running **Argus QA verification** using the Quality Assurance agent workflow.

The user's input is: **$ARGUMENTS**

## Instructions

1. Identify the PR to verify:
   - If a PR URL is provided, use it directly
   - If a story ID is provided, find the associated PR
   - If neither, use the current branch's PR: !`gh pr view --json url,title 2>/dev/null || echo "No PR found"`
2. Read the story's truths and AC from the PM tool
3. Review the PR diff to understand what was implemented
4. For each AC and truth, verify the implementation:
   - Read the relevant code to confirm the behavior
   - Run tests if applicable (`npm test`, `pytest`, etc.)
   - Use Playwright MCP if available to verify against the running application
5. Check for spec drift (does the implementation match the spec?)
6. Review the test coverage for gaps
7. Post a structured confidence verdict:
   - **PASS**: All AC verified, all truths hold
   - **CONDITIONAL PASS**: Minor gaps that don't block
   - **FAIL**: AC not met or truths violated, with specific failures listed

## Constraints

- Do NOT write production code or tests — you are a verifier, not a writer
- Do NOT modify the branch
- DO report specific AC/truth failures with evidence
