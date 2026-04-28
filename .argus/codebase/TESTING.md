# Testing

## Current State

**No tests exist.** There are no test files, no test framework configured, and no CI/CD pipeline.

## Test Frameworks

- None installed or configured
- No `pytest`, `unittest`, or any test runner in `requirements.txt`
- No test directories (`tests/`, `test/`, etc.)

## CI/CD

- No CI workflow files (`.github/workflows/` directory does not exist)
- Only `.github/PULL_REQUEST_TEMPLATE.md` exists

## Coverage

- No coverage tooling configured

## Recommended Setup

- **Framework:** pytest + pytest-asyncio (for FastAPI async endpoints)
- **HTTP testing:** httpx with FastAPI's TestClient
- **Coverage:** pytest-cov
- **CI:** GitHub Actions workflow for lint + test
