# Plan: As a developer, I can run Ruff to check and format code so that style is consistent

**Story**: #23
**Spec**: docs/specs/test-framework-setup.md (US5)
**Branch**: feature/23-ruff-linting-setup
**Date**: 2026-03-14
**Mode**: Standard — tooling config, no business logic to TDD

## Technical Decisions

### TD-1: Line length 120
- **Context**: Need a line length that fits the project's existing style
- **Decision**: 120 characters — wide enough for FastAPI decorators and Pydantic fields
- **Alternatives considered**: 88 (Ruff default), 100, 79 (PEP 8 strict)

### TD-2: Double quotes
- **Context**: Need consistent quote style
- **Decision**: Double quotes (Ruff default, matches existing code)
- **Alternatives considered**: Single quotes

## Files to Create or Modify

- `requirements-dev.txt` — add ruff dependency
- `pyproject.toml` — add Ruff configuration sections
- `backend/**/*.py`, `config.py`, `run.py`, `transcriber.py`, `tests/**/*.py` — fix violations

## Approach per AC

### AC 1: Ruff added as a dev dependency
Add `ruff>=0.9.0` to `requirements-dev.txt` and install.

### AC 2: pyproject.toml contains Ruff config
Add `[tool.ruff]`, `[tool.ruff.lint]`, and `[tool.ruff.format]` sections.

### AC 3 & 4: All existing code passes, violations fixed
Run `ruff check --fix .` and `ruff format .` to auto-fix, then manually fix remaining issues.

## Commit Sequence

1. Add Ruff config and dev dependency
2. Fix linting violations
3. Fix formatting violations

## Risks and Trade-offs

- Import reordering (I rules) is safe but may produce a noisy diff

## Deviations from Spec

- None anticipated

## Deviations from Plan

_Populated after implementation._
