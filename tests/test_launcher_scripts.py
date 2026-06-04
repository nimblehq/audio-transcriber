"""Syntax guard for the macOS launcher shell scripts.

`bash -n` only parses (it never executes), so this is a syntax-only regression
guard with near-zero behavioral coverage. The behavioral acceptance criteria
(double-click, browser opens, quit terminates uvicorn) require manual macOS
verification. Skips gracefully when bash is unavailable (e.g. some CI images).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SHELL_SCRIPTS = [
    REPO_ROOT / "scripts" / "launch.sh",
    REPO_ROOT / "scripts" / "stop.sh",
]


@pytest.mark.unit
@pytest.mark.parametrize("script", SHELL_SCRIPTS, ids=lambda path: path.name)
def test_shell_script_has_valid_syntax(script: Path) -> None:
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash is not available")
    assert script.exists(), f"missing script: {script}"
    result = subprocess.run(
        [bash, "-n", str(script)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
