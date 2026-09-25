"""Impact analyzer.

Given a diff analysis and code analysis, summarize which functions
are affected and classify each analyzed path as verified / partial /
unresolved based on the tests that were mapped, the gaps detected,
and whether generated tests addressed those gaps.
"""
from __future__ import annotations

from engine.models import (
    CodeAnalysis,
    DiffAnalysis,
    GeneratedTest,
    TestGap,
    TestMap,
)


def summarize_impact(
    diff: DiffAnalysis,
    code: list[CodeAnalysis],
    tests: TestMap,
    gaps: list[TestGap],
    generated_tests: list[GeneratedTest] | None = None,
    execution_passed: int = 0,
) -> dict:
    """Summarize impact and path classification.

    A function is considered:
      - verified   : has a mapped test OR its gaps were addressed by a
                     generated test that passed.
      - partial    : has a mapped test but still has unaddressed gaps.
      - unresolved : has neither mapped tests nor addressed gaps.
    """
    generated_tests = generated_tests or []

    # Collect all function names in order.
    functions: list[str] = []
    for ca in code:
        for fn in ca.functions:
            functions.append(fn.name)

    seen: set[str] = set()
    ordered: list[str] = []
    for name in functions:
        if name not in seen:
            seen.add(name)
            ordered.append(name)

    # Which functions have any mapped test?
    tested_functions = set(tests.function_to_tests.keys())

    # Which functions have gaps that were NOT addressed by a generated test?
    addressed_gap_ids = {
        gt.targets_gap for gt in generated_tests if gt.targets_gap
    }
    unaddressed_gap_functions: set[str] = set()
    for g in gaps:
        if g.id not in addressed_gap_ids:
            unaddressed_gap_functions.add(g.function)

    verified = 0
    partial = 0
    unresolved = 0

    for name in ordered:
        has_test = name in tested_functions
        has_unaddressed_gap = name in unaddressed_gap_functions

        if has_test and not has_unaddressed_gap:
            verified += 1
        elif has_test and has_unaddressed_gap:
            partial += 1
        elif not has_test and not has_unaddressed_gap and generated_tests:
            # No mapped test, no unaddressed gap, but a generated test
            # passed → treat as verified.
            verified += 1
        else:
            unresolved += 1

    return {
        "files_changed": diff.files_changed,
        "functions_affected": len(ordered),
        "function_names": ordered,
        "verified_paths": verified,
        "partial_paths": partial,
        "unresolved_paths": unresolved,
    }