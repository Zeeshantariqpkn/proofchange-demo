"""Test runner.

Executes pytest against a target directory and captures structured
results. This module only runs code inside a controlled directory —
it is never exposed as an arbitrary command executor.
"""
from __future__ import annotations

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


def run_pytest(
    target_dir: str,
    extra_args: Optional[list[str]] = None,
    timeout_s: int = 60,
) -> ExecutionResult:
    """Run pytest inside `target_dir`. Returns structured results."""
    result = ExecutionResult()
    if not os.path.isdir(target_dir):
        result.exit_code = 2
        result.stderr = f"target_dir does not exist: {target_dir}"
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
        result.stderr = f"pytest timed out after {timeout_s}s: {exc}"
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