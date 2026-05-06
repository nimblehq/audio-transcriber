# Plan: Switch to the Argus Claude plugin

**Story**: #60
**Spec**: N/A (chore)
**Branch**: feature/60-switch-to-argus-plugin
**Date**: 2026-05-06
**Mode**: Standard — pure config/file removal, no logic to test

## Technical Decisions

### TD-1: Delete `.claude/settings.json` rather than leave an empty `{}`
- **Context**: After removing the Argus `PreToolUse` hook block, the file contains no other keys. The issue's example final state shows `enabledMcpjsonServers`, but this project has no `.mcp.json` and no such block today — that example is generic, not project-specific.
- **Decision**: Remove the file entirely. `.claude/settings.local.json` stays (non-Argus permissions allowlist).
- **Alternatives considered**: Leave `{}` in place. Rejected as noise — Claude Code does not require the file to exist.

## Files to Create or Modify

- Delete `.claude/agents/` — Argus agent definitions, now provided by the global plugin
- Delete `.claude/commands/argus/` and the resulting empty `.claude/commands/` dir — Argus slash commands now global
- Delete `.claude/hooks/context-monitor.sh` and the resulting empty `.claude/hooks/` dir — context monitor hook now global
- Edit `package.json` — remove `argus-monorepo` from `devDependencies`
- Regenerate `package-lock.json` via `npm install`
- Delete `.claude/settings.json` — only contained the Argus `PreToolUse` hook block

## Approach per AC

No AC (chore). Follows the Delete/Keep/Add checklist in issue #60.

## Commit Sequence

1. `[#60] Remove Argus agents, commands, and hooks from .claude/`
2. `[#60] Remove argus-monorepo dev dependency`
3. `[#60] Remove Argus PreToolUse hook from settings.json`

## Risks and Trade-offs

- The deleted `.claude/settings.json` will not be re-created automatically. If a future need arises for project-level Claude Code settings, a fresh file can be added.
- `npm install` regenerates the lockfile; transitive dependency entries previously pulled in only by `argus-monorepo` will disappear. That is the intended cleanup.

## Deviations from Plan

- **Deleted `package.json` and `package-lock.json` entirely** rather than editing `package.json` to remove the dep and running `npm install` to refresh the lockfile. Rationale: this is a Python project, and `argus-monorepo` was the sole entry. Leaving an empty `{}` `package.json` plus a near-empty lockfile would add dead weight with no purpose. The issue's checklist literal step ("argus from package.json devDependencies, then reinstall to update lockfile") describes the mechanics for projects where other deps exist; the spirit is "remove the dep and its lockfile artifacts," which a clean delete also satisfies.
