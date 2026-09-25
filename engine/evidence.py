"""Evidence engine.

Aggregates the analysis pipeline into a single Change Evidence Package
and computes an evidence strength level using transparent rules.
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from engine.models import (
    CodeAnalysis,
    DiffAnalysis,
    EvidencePackage,
    ExecutionResult,
    GeneratedTest,
    TestGap,
    TestMap,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compute_level(
    gaps: list[TestGap],
    generated_tests: list[GeneratedTest],
    execution: ExecutionResult,
    analyzed_paths: int,
    verified_paths: int,
) -> tuple[str, str]:
    """Return (level, rationale).

    Rules (transparent, conservative):
      - INSUFFICIENT: no execution evidence at all, or any failing test.
      - PARTIAL: execution succeeded but some gaps remain unaddressed by
        a passing generated test, or fewer than 70% of analyzed paths
        are verified.
      - STRONG: execution succeeded, every detected gap is targeted by a
        generated test, and at least 70% of analyzed paths are verified.
    """
    if execution.total == 0:
        return "INSUFFICIENT", "No tests were executed."
    if execution.failed > 0:
        return "INSUFFICIENT", f"{execution.failed} test(s) failed."

    targeted = {g.targets_gap for g in generated_tests if g.targets_gap}
    unaddressed = [g for g in gaps if g.id not in targeted]
    high = [g for g in gaps if g.severity == "high"]

    if high:
        return "PARTIAL", f"{len(high)} high-severity gap(s) remain."

    ratio = (verified_paths / analyzed_paths) if analyzed_paths else 0.0
    if unaddressed or ratio < 0.7:
        return (
            "PARTIAL",
            f"{len(unaddressed)} gap(s) remain unaddressed; "
            f"{verified_paths}/{analyzed_paths} paths verified.",
        )
    return (
        "STRONG",
        f"All executed tests passed; {len(gaps)} gap(s) addressed; "
        f"{verified_paths}/{analyzed_paths} analyzed paths verified.",
    )


def build_package(
    *,
    diff: DiffAnalysis,
    code_analyses: list[CodeAnalysis],
    tests: TestMap,
    gaps: list[TestGap],
    generated_tests: list[GeneratedTest],
    execution: ExecutionResult,
    impact: dict[str, Any],
    repository: str = "demo_repo",
    commit: str = "",
    pr_number: int | None = None,
    pr_title: str = "",
    ai_mode: str = "documented_bob_workflow",
) -> EvidencePackage:
    """Build the Change Evidence Package."""

    existing_tests = len(tests.all_tests)

    analyzed_paths = impact.get("functions_affected", 0) or 1
    verified = impact.get("verified_paths", 0)
    partial = impact.get("partial_paths", 0)
    unresolved = impact.get("unresolved_paths", 0)

    level, rationale = _compute_level(
        gaps, generated_tests, execution, analyzed_paths, verified
    )

    pkg = EvidencePackage(
        id=str(uuid.uuid4()),
        created_at=_now_iso(),
        repository=repository,
        commit=commit,
        pr_number=pr_number,
        pr_title=pr_title,
        ai_mode=ai_mode,
        ai_assisted_steps=[
            "repository_understanding",
            "test_generation",
            "verification_summary",
        ],
        change={
            "files_changed": diff.files_changed,
            "functions_affected": impact.get("functions_affected", 0),
            "function_names": impact.get("function_names", []),
        },
        testing={
            "existing_tests": existing_tests,
            "test_gaps": len(gaps),
            "generated_tests": len(generated_tests),
        },
        execution={
            "tests_executed": execution.total,
            "passed": execution.passed,
            "failed": execution.failed,
            "skipped": execution.skipped,
            "duration_s": round(execution.duration_s, 3),
        },
        paths={
            "verified": verified,
            "partial": partial,
            "unresolved": unresolved,
        },
        evidence={
            "level": level,
            "rationale": rationale,
        },
        artifacts={
            "diff": diff.to_dict(),
            "code": [c.to_dict() for c in code_analyses],
            "tests": tests.to_dict(),
            "gaps": [g.to_dict() for g in gaps],
            "generated_tests": [g.to_dict() for g in generated_tests],
            "execution_stdout": execution.stdout,
            "execution_stderr": execution.stderr,
        },
    )
    return pkg


def save_package(pkg: EvidencePackage, data_dir: str) -> str:
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, f"{pkg.id}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(pkg.to_dict(), fh, indent=2)
    return path


def to_markdown(pkg: EvidencePackage) -> str:
    d = pkg.to_dict()
    lines = [
        f"# Change Evidence — {pkg.id}",
        "",
        f"- Repository: `{pkg.repository}`",
        f"- Commit: `{pkg.commit or 'n/a'}`",
        f"- PR: #{pkg.pr_number}" if pkg.pr_number else "- PR: n/a",
        f"- Created: {pkg.created_at}",
        f"- AI mode: `{pkg.ai_mode}`",
        "",
        "## Change",
        f"- Files changed: {d['change']['files_changed']}",
        f"- Functions affected: {d['change']['functions_affected']}",
        "",
        "## Testing",
        f"- Existing tests mapped: {d['testing']['existing_tests']}",
        f"- Test gaps: {d['testing']['test_gaps']}",
        f"- Generated tests: {d['testing']['generated_tests']}",
        "",
        "## Execution",
        f"- Executed: {d['execution']['tests_executed']}",
        f"- Passed: {d['execution']['passed']}",
        f"- Failed: {d['execution']['failed']}",
        f"- Duration: {d['execution']['duration_s']}s",
        "",
        "## Paths",
        f"- Verified: {d['paths']['verified']}",
        f"- Partial: {d['paths']['partial']}",
        f"- Unresolved: {d['paths']['unresolved']}",
        "",
        f"## Evidence: **{d['evidence']['level']}**",
        "",
        f"_{d['evidence']['rationale']}_",
        "",
    ]
    return "\n".join(lines)