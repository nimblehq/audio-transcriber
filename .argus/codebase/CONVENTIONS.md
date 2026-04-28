# Coding Conventions

## Python (Backend)

- **Style:** PEP 8, snake_case for functions/variables
- **Type hints:** Modern syntax (`list[str]`, `str | None`) with `from __future__ import annotations`
- **Models:** Pydantic `BaseModel` for all data structures with `Field` defaults
- **Enums:** `str, Enum` pattern for serializable enums
- **Imports:** Standard lib → third-party → local, heavy ML deps imported lazily inside functions
- **Error handling:** Broad try/except in transcription pipeline, logger.exception for errors
- **File I/O:** `pathlib.Path` throughout, `json.dump/load` for persistence

## JavaScript (Frontend)

- **Style:** No framework, vanilla ES6, global functions
- **State:** Global variables (`currentAudio`, `pollInterval`, `autoScroll`)
- **DOM:** Template literals for HTML generation, `innerHTML` assignment
- **API calls:** Centralized in `api.js` with fetch wrapper
- **Naming:** camelCase for functions/variables
- **Components:** Each component is a self-contained JS file with render function

## Project Conventions

- **No build step** — no transpilation, bundling, or minification
- **Linter/Formatter:** Ruff (`ruff check` + `ruff format`) for Python, configured in `pyproject.toml`. No frontend linter/formatter
- **No type checking** — no mypy or TypeScript
- **Git:** Gitflow branching model, `develop` as main branch
- **Commits:** Conventional-style commit messages
