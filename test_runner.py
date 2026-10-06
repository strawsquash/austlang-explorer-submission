"""Run the fixed project test suite from the app's Tests view."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).parent


def run_project_tests(timeout_seconds: int = 20) -> tuple[bool, str]:
    """Run only this project's checked-in tests; never execute user input."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", str(PROJECT_DIR / "tests")],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False, f"Tests exceeded the {timeout_seconds}-second limit."
    except OSError as exc:
        return False, f"Tests could not start: {exc}"
    output = (result.stdout + "\n" + result.stderr).strip()
    return result.returncode == 0, output or "The test process returned no output."
