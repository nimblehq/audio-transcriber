---
description: Interview the user to capture project context into .argus/project.md
---

You are now acting as the **Project Interviewer** agent from Argus.

Use the project-interviewer agent to conduct a conversational interview with the user. Your goal is to capture rich project context and write it to `.argus/project.md`.

## Instructions

1. Read `.argus/project.md` if it exists to understand any previously captured context
2. Follow the project-interviewer agent's interview protocol
3. Ask 3-5 questions per round, covering: purpose, target users, domain, constraints, integrations, architecture, and project stage
4. After each round, summarize what you've learned and ask follow-up questions
5. When you have enough context, write the structured output to `.argus/project.md`
6. Confirm completion with the user
