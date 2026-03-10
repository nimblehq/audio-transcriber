---
description: Systematic bug investigation with persistent debug log
argument-hint: "[bug description or issue URL]"
---

You are now running **Argus debug mode** using the Debug agent workflow.

The user's input is: **$ARGUMENTS**

## Instructions

### Setup

1. Check for an existing debug session at `.argus/debug/session.md`
   - If it exists, ask the user whether to resume or start fresh
   - If starting fresh, archive the old session
2. Create `.argus/debug/session.md` with the bug description

### Investigation (Scientific Method)

3. **Gather symptoms**: Expected vs. actual behavior, error messages, reproduction steps
4. **Form hypotheses**: List possible root causes ranked by likelihood
5. **Test hypotheses systematically**:
   - Start with the most likely hypothesis
   - Use binary search through the problem space
   - Log each test and its result in the session file (append-only)
6. **Eliminate disproven paths**: Mark hypotheses as eliminated with evidence
7. **Identify root cause**: When a hypothesis is confirmed, document it

### Resolution

8. Present the root cause and recommended fix to the user
9. If the user approves, implement the fix
10. Update the session file with the resolution

## Session File Format

The session file at `.argus/debug/session.md` is append-only:

```markdown
# Debug Session: [bug description]

## Symptoms
[Expected vs actual behavior]

## Hypotheses
1. [hypothesis] — Status: [testing/eliminated/confirmed]

## Evidence Log
### [timestamp] Test: [what was tested]
Result: [what happened]
Conclusion: [what this means]
```

## Constraints

- Never delete entries from the evidence log — append only
- Log every test and its result, even negative results
- If stuck after 3 attempts on the same hypothesis, move to the next one
