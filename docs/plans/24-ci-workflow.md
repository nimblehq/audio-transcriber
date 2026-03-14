# Plan: CI Workflow Setup

**Story**: #24
**Spec**: docs/specs/test-framework-setup.md (US6, US7)
**Branch**: feature/24-ci-workflow
**Date**: 2026-03-14
**Mode**: Standard — infrastructure config, no application code

## Technical Decisions

### TD-1: Dependency installation in CI
- **Context**: requirements.txt includes whisperx (git+https) and torch, which are large and need GPU
- **Decision**: Use a separate `requirements-ci.txt` that excludes ML dependencies, since all tests mock them
- **Alternatives considered**: Filtering requirements.txt with grep — fragile; installing everything — slow and unnecessary

### TD-2: Ruff installation
- **Context**: Ruff is not yet in requirements.txt but pyproject.toml already configures it
- **Decision**: Add ruff to dev dependencies in requirements.txt
- **Alternatives considered**: Install only in CI — would force devs to install separately

## Files to Create or Modify

- `requirements.txt` — add ruff to dev dependencies
- `.github/workflows/ci.yml` — GitHub Actions workflow

## Approach per AC

### AC 1-2: Workflow file and triggers
Create `.github/workflows/ci.yml` triggered on PRs to develop and main

### AC 3-6: CI steps
Checkout, Python 3.12, install deps (excluding ML packages), ruff check, ruff format --check, pytest --cov with fail_under=80

### AC 7: Ruff in dev dependencies
Add ruff to requirements.txt under dev dependencies section

## Commit Sequence

1. Add ruff to dev dependencies
2. Add GitHub Actions CI workflow

## Risks and Trade-offs

- Coverage threshold may not be met with current test suite — pyproject.toml already sets fail_under=80

## Deviations from Spec

- Spec mentions branch protection documentation (US7) — skipping as it's a manual GitHub settings task, not code

## Deviations from Plan

_Populated after implementation._
