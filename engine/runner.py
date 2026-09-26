"""Test runner.

Executes pytest against a target directory and captures structured
results. This module only runs code inside a controlled directory —
it is never exposed as an arbitrary command executor.
"""
from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
import time
from typing import Optional

from engine.models import ExecutionResult

# Match pytest summary lines like:
#   "3 passed in 0.12s"
#   "2 passed, 1 failed, 1 skipped in 0.20s"
_SUMMARY_RE = re.compile(r"(\d+)\s+(passed|failed|skipped|error|errors)")

# Exit-code used by this module when pytest itself is missing.
_EXIT_PYTEST_NOT_FOUND = 127

# Marker written into stderr for syntax errors detected before the run.
_SYNTAX_ERROR_PREFIX = "SyntaxError in test file"


def _pytest_available() -> bool:
    """Return True if pytest is importable in the current Python environment."""
    return importlib.util.find_spec("pytest") is not None


def _check_test_files_syntax(target_dir: str) -> Optional[str]:
    """Scan every test_*.py / *_test.py file in *target_dir* for syntax errors.

    Returns the first error message found, or None if all files are clean.
    Only the top-level directory is scanned (no recursion) to stay fast.
    """
    try:
        entries = os.listdir(target_dir)
    except OSError:
        return None

    for name in sorted(entries):
        if not (name.startswith("test_") or name.endswith("_test.py")):
            continue
        if not name.endswith(".py"):
            continue
        filepath = os.path.join(target_dir, name)
        with open(filepath, encoding="utf-8", errors="replace") as fh:
            source = fh.read()
        try:
            compile(source, filepath, "exec")
        except SyntaxError as exc:
            return (
                f"{_SYNTAX_ERROR_PREFIX}: {filepath} "
                f"(line {exc.lineno}): {exc.msg}"
            )
    return None


def run_pytest(
    target_dir: str,
    extra_args: Optional[list[str]] = None,
    timeout_s: int = 60,
) -> ExecutionResult:
    """Run pytest inside *target_dir* and return structured results.

    Three failure modes are handled explicitly before launching the
    subprocess so that callers always receive a descriptive ``stderr``
    and a meaningful ``exit_code``:

    * **pytest not found** – exit_code 127, mirrors the POSIX "command not
      found" convention.
    * **syntax error** – exit_code 3 (distinct from pytest's own codes 0–2),
      stderr contains the offending file and line number.
    * **timeout** – exit_code 124 (mirrors the GNU ``timeout`` utility),
      stderr records the elapsed limit.
    """
    result = ExecutionResult()

    if not os.path.isdir(target_dir):
        result.exit_code = 2
        result.stderr = f"target_dir does not exist: {target_dir}"
        return result

    # --- Guard: pytest must be installed ---------------------------------------
    if not _pytest_available():
        result.exit_code = _EXIT_PYTEST_NOT_FOUND
        result.stderr = (
            "pytest is not installed in the current Python environment "
            f"({sys.executable}). Install it with: pip install pytest"
        )
        return result

    # --- Guard: pre-flight syntax check ---------------------------------------
    syntax_error = _check_test_files_syntax(target_dir)
    if syntax_error:
        result.exit_code = 3
        result.stderr = syntax_error
        return result

    args = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "--no-header",
        "-p",
        "no:cacheprovider",
    ]
    if extra_args:
        args.extend(extra_args)

    start = time.monotonic()
    try:
        proc = subprocess.run(  # noqa: S603 - controlled invocation
            args,
            cwd=target_dir,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        result.exit_code = 124
        result.stderr = (
            f"pytest timed out after {timeout_s}s — "
            "consider raising timeout_s or reducing the test suite scope. "
            f"Detail: {exc}"
        )
        result.duration_s = time.monotonic() - start
        return result
    except FileNotFoundError:
        # sys.executable itself is somehow missing — extremely rare but safe.
        result.exit_code = _EXIT_PYTEST_NOT_FOUND
        result.stderr = f"Python interpreter not found: {sys.executable}"
        result.duration_s = time.monotonic() - start
        return result

    result.duration_s = time.monotonic() - start
    result.exit_code = proc.returncode
    result.stdout = proc.stdout
    result.stderr = proc.stderr

    combined = f"{proc.stdout}\n{proc.stderr}"
    for count, kind in _SUMMARY_RE.findall(combined):
        n = int(count)
        if kind == "passed":
            result.passed += n
        elif kind == "failed":
            result.failed += n
        elif kind == "skipped":
            result.skipped += n

    result.total = result.passed + result.failed + result.skipped
    return result