# Plan: Migrate from Gitflow to trunk-based development

**Story**: #44
**Spec**: docs/specs/trunk-based-development.md
**Branch**: feature/44-trunk-based-development
**Date**: 2026-04-28
**Mode**: Standard — repo configuration, CI filter, and docs only; no application logic to test.

## Technical Decisions

### TD-1: Consolidation via PR merge-commit instead of direct fast-forward push
- **Context**: Spec step 2 asks for `git merge --ff-only develop` followed by `git push origin main`. The repository already has an active ruleset on `main` (id 12242796) that blocks all direct pushes (`Changes must be made through a pull request`) with no bypass actor. The maintainer would have to disable the rule and re-enable it around a manual push, opening a window where `main` is unprotected.
- **Decision**: Use the spec's documented fallback path (step 2: "If FF is not possible, fall back to a merge commit"). Branch `feature/44-trunk-based-development` is cut off `develop`, so it carries the full 20-commit consolidation. The PR targets `main` and is merged with GitHub's "Create a merge commit" option. All 24 commit SHAs (20 develop + 4 migration) land on `main` with original history.
- **Alternatives considered**:
  - FF + direct push: blocked by ruleset, no admin bypass available.
  - Two PRs (consolidation, then story): doubles the work for the same final state.
  - Squash-merge of this PR: would collapse 20 already-reviewed stories into one commit, losing history.

### TD-2: README left untouched
- **Context**: AC requires that README no longer references Gitflow, `develop`, or release branches.
- **Decision**: `grep -i -E "gitflow|develop|release branch"` against `README.md` returned no Gitflow-related matches (only one false positive on the word "developer" in a Homebrew description). The AC is already satisfied; no edits needed.
- **Alternatives considered**: Adding a "Contributing" section describing trunk-based flow — out of scope; the spec keeps that in `CLAUDE.md`.

### TD-3: CHANGELOG seeded from existing tags only
- **Context**: AC requires `CHANGELOG.md` seeded with `1.0.0` and `1.1.0` "best-effort from `git log`".
- **Decision**: Two release entries with dates pulled from tag commits (both 2026-02-26) and bullet summaries derived from the commits between tags. No "Unreleased" content beyond a placeholder section.

## Files to Create or Modify

- `.github/workflows/ci.yml` — change `branches:` filters from `[develop, main]` to `[main]` for `push` and `pull_request`.
- `CLAUDE.md` — append a `## Git Workflow` section describing the trunk-based flow and explicitly overriding the global "Always follow Gitflow" instruction (BR-10).
- `CHANGELOG.md` (new) — Keep a Changelog format, seeded with `1.0.0` and `1.1.0`.
- `docs/plans/44-trunk-based-development.md` (this file).

## Approach per AC

### AC: `main` contains every commit on `develop` at migration time
PR is sourced from `feature/44-trunk-based-development` (off `develop`); merged via "Create a merge commit" preserves all 20 develop commits on `main`.

### AC: `main` is GitHub default branch
Post-merge admin step: `gh api -X PATCH /repos/nimblehq/audio-transcriber -f default_branch=main`.

### AC: `develop` is deleted locally and remotely
Post-merge admin step: `git push origin --delete develop && git branch -D develop`. Ruleset on `develop` (none currently) does not block deletion.

### AC: CI filters target `main` only
Edit `ci.yml` in this PR.

### AC: Branch protection on `main`
Post-merge admin: replace existing ruleset with one that requires `Lint & Format` + `Test & Coverage` checks, linear history, and squash-only merges. Repo merge methods updated via `gh api -X PATCH /repos/.../...` to disable merge-commit and rebase-merge.

### AC: `CLAUDE.md` Git Workflow section overrides global Gitflow rule
Edit `CLAUDE.md` in this PR.

### AC: `README.md` no Gitflow references
Already satisfied — verified with grep. No edit needed.

### AC: `CHANGELOG.md` exists with `1.0.0` and `1.1.0`
New file in this PR.

### AC: Open PRs targeting `develop` retargeted before delete
`gh pr list --base develop` returned empty at planning time. Re-checked just before delete.

### AC: Direct push to `main` rejected
Already enforced by existing ruleset; will remain so under the new branch protection.

### AC: CI runs on PRs to `main`
Workflow already defines `Lint & Format` and `Test & Coverage`; new branch protection requires both as status checks.

### AC: Tags `1.0.0`, `1.1.0` preserved
No tag operations are performed; tags remain attached to their original commits, which stay in `main`'s ancestry after the merge.

## Commit Sequence

1. `[#44] Add plan for trunk-based development migration`
2. `[#44] Update CI workflow to target main only`
3. `[#44] Add Git Workflow section to CLAUDE.md`
4. `[#44] Add CHANGELOG.md seeded with 1.0.0 and 1.1.0`

## Post-merge admin steps (executed by maintainer with `gh`)

1. Set default branch to `main`.
2. Disable merge-commit and rebase-merge on the repo (squash only).
3. Replace ruleset / configure branch protection on `main`:
   - Require PR, 0 approvals.
   - Require `Lint & Format` and `Test & Coverage` status checks.
   - Require linear history.
   - Allow squash only.
4. `gh pr list --base develop` — retarget any PRs that landed in the meantime.
5. Delete `develop` (remote then local).
6. Prune merged `feature/*` and `release/*` remote branches.

## Risks and Trade-offs

- **Big-PR diff**: this PR shows 24 commits + 4 file changes. Mitigated by clear PR description and the fact that 20 of the commits are already-reviewed merges.
- **Merge-commit on `main`**: introduces one merge commit during the migration. Subsequent PRs will be squash-only per BR-13/14. The single migration merge commit is the documented spec fallback.
- **Stale local feature branches**: pruning is opportunistic in step 11 of the spec; not all local branches will be touched.

## Deviations from Spec

- **Step 2 (consolidation)**: spec prefers `git merge --ff-only` + direct push; I'm using the spec-documented merge-commit fallback because the existing repo ruleset blocks direct pushes to `main` with no bypass. Net result on `main` is identical (every develop commit reaches `main`); only the merge method differs.

## Deviations from Plan

_Populated after implementation._
