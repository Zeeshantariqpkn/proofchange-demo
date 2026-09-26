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
from engine.impact_analyzer import PathSummary


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
    unaddressed_high = [g for g in unaddressed if g.severity == "high"]

    if unaddressed_high:
        return "PARTIAL", f"{len(unaddressed_high)} high-severity gap(s) remain unaddressed."

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
    impact: PathSummary,
    repository: str = "demo_repo",
    commit: str = "",
    pr_number: int | None = None,
    pr_title: str = "",
    ai_mode: str = "documented_bob_workflow",
) -> EvidencePackage:
    """Build the Change Evidence Package."""

    existing_tests = len(tests.all_tests)

    analyzed_paths = impact.functions_affected or 1
    verified = impact.verified_paths
    partial = impact.partial_paths
    unresolved = impact.unresolved_paths

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
            "functions_affected": impact.functions_affected,
            "function_names": impact.function_names,
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


def simulate_with_generated_tests(
    pkg: EvidencePackage,
    additional_tests: list[GeneratedTest],
) -> tuple[str, str]:
    """Return the (level, rationale) the package WOULD have if *additional_tests*
    were merged and all currently-passing tests still pass.

    The simulation is a pure projection: no files are written and no
    subprocess is launched.  The execution counters are optimistically
    bumped by the number of additional tests (all assumed to pass), and
    the full gap list is re-evaluated with the combined generated set.

    ``verified_paths`` is also projected: any function that was previously
    *partial* (has a mapped test but an unaddressed gap) becomes *verified*
    once all of its gaps are targeted by the combined generated set.

    Args:
        pkg:              The current Change Evidence Package.
        additional_tests: Generated tests to simulate as merged (typically
                          the one test produced for a specific gap).

    Returns:
        A ``(level, rationale)`` tuple identical in shape to what
        :func:`_compute_level` returns.
    """
    d = pkg.to_dict()
    gaps = [
        TestGap(**{k: v for k, v in g.items()})
        for g in d["artifacts"]["gaps"]
    ]
    existing_gen = [
        GeneratedTest(**{k: v for k, v in gt.items()})
        for gt in d["artifacts"]["generated_tests"]
    ]
    combined = existing_gen + additional_tests

    ex = d["execution"]
    sim_execution = ExecutionResult(
        exit_code=0,
        total=ex["tests_executed"] + len(additional_tests),
        passed=ex["passed"] + len(additional_tests),
        failed=ex["failed"],
        skipped=ex["skipped"],
        duration_s=ex["duration_s"],
    )

    analyzed_paths = d["change"]["functions_affected"] or 1
    paths = d["paths"]

    # Project verified_paths: functions that were partial (mapped test + gap)
    # become verified if all their gaps are now targeted by the combined set.
    combined_targeted = {gt.targets_gap for gt in combined if gt.targets_gap}
    extra_verified = 0
    if additional_tests:
        # For each function currently in partial state, check whether all of
        # its gaps are now covered by the combined generated set.
        partial_functions: set[str] = set()
        for g in gaps:
            if g.id not in {gt.targets_gap for gt in existing_gen if gt.targets_gap}:
                partial_functions.add(g.function)
        for fn_name in partial_functions:
            fn_gaps = [g for g in gaps if g.function == fn_name]
            if all(g.id in combined_targeted for g in fn_gaps):
                extra_verified += 1

    verified_paths = paths["verified"] + extra_verified

    return _compute_level(gaps, combined, sim_execution, analyzed_paths, verified_paths)


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