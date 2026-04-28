---
description: Analyze the codebase into structured documentation in .argus/codebase/
---

You are now running **Argus codebase mapping**. Analyze the existing codebase and produce structured documentation that all downstream agents reference.

## Instructions

Use the codebase-mapper agent via Task to analyze the codebase across four focus areas. Run them in parallel when possible:

### Focus Area 1: Tech & Stack
- Identify languages, frameworks, and dependencies
- Document build tools, package managers, and runtime versions
- Map external service integrations
- Output: `.argus/codebase/STACK.md` and `.argus/codebase/INTEGRATIONS.md`

### Focus Area 2: Architecture
- Map the project structure (directories, modules, entry points)
- Identify architectural patterns (MVC, hexagonal, microservices, etc.)
- Document data flow and key abstractions
- Output: `.argus/codebase/ARCHITECTURE.md` and `.argus/codebase/STRUCTURE.md`

### Focus Area 3: Quality & Testing
- Identify test frameworks, coverage tools, and CI setup
- Map existing test patterns (unit, integration, e2e)
- Document coding conventions observed in the codebase
- Output: `.argus/codebase/TESTING.md` and `.argus/codebase/CONVENTIONS.md`

### Focus Area 4: Concerns
- Identify technical debt and known issues
- Flag security concerns
- Note performance bottlenecks or scaling risks
- Output: `.argus/codebase/CONCERNS.md`

## After Mapping

1. Report a summary of what was documented
2. Highlight any significant concerns found
3. Suggest next steps (e.g., "Run `/argus:describe` to capture project context")
