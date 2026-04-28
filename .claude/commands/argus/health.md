---
description: Check project health and Argus configuration
---

You are now running **Argus health check**. Validate the `.argus/` directory and project configuration.

## Instructions

Run the `argus health` CLI command and report the results:

!`npx argus health 2>&1`

If the health check reports issues, suggest fixes for each one. If the `--repair` flag would help, recommend running `argus health --repair`.

## Manual Checks

If the CLI is not available, perform these checks manually:

1. **Config validation**: Read `.argus/config.yml` and verify:
   - `pm_tool` is set to a valid value (shortcut, linear, jira, github_projects)
   - `stacks` contains at least one entry
   - `commit_prefix` is set
   - All required sections exist (workflow, parallelization, gates, safety)

2. **Codebase docs freshness**: Check if `.argus/codebase/` files exist:
   - ARCHITECTURE.md, CONVENTIONS.md, STRUCTURE.md, TESTING.md
   - Flag any that are missing (suggest running `/argus:map-codebase`)

3. **Project context**: Check if `.argus/project.md` exists
   - If missing, suggest running `/argus:describe`

4. **Security hygiene**:
   - No secrets in `config.yml`
   - No command injection in hook scripts
