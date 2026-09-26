"""Impact analyzer.

Given a diff analysis and code analysis, summarize which functions
are affected and classify each analyzed path as verified / partial /
unresolved based on the tests that were mapped, the gaps detected,
and whether generated tests addressed those gaps.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from engine.models import (
    CodeAnalysis,
    DiffAnalysis,
    GeneratedTest,
    TestGap,
    TestMap,
)


@dataclass
class PathSummary:
    """Typed summary returned by summarize_impact."""
    files_changed: int
    functions_affected: int
    function_names: list[str]
    verified_paths: int
    partial_paths: int
    unresolved_paths: int

    def to_dict(self) -> dict:
        return {
            "files_changed": self.files_changed,
            "functions_affected": self.functions_affected,
            "function_names": self.function_names,
            "verified_paths": self.verified_paths,
            "partial_paths": self.partial_paths,
            "unresolved_paths": self.unresolved_paths,
        }


def summarize_impact(
    diff: DiffAnalysis,
    code: list[CodeAnalysis],
    tests: TestMap,
    gaps: list[TestGap],
    generated_tests: list[GeneratedTest] | None = None,
    execution_passed: int = 0,
) -> PathSummary:
    """Summarize impact and path classification.

    A function is considered:
      - verified   : has a mapped test OR all its gaps were addressed by
                     generated tests that passed.
      - partial    : has a mapped test but still has unaddressed gaps.
      - unresolved : has neither mapped tests nor addressed gaps.
    """
    generated_tests = generated_tests or []

    # Collect all function names in order, keyed by (file_path, name) to
    # avoid silently dropping same-named functions from different files.
    # The display name remains the bare function name; deduplication is
    # per-file so both occurrences are counted.
    functions: list[tuple[str, str]] = []  # (source_path, fn_name)
    for ca in code:
        for fn in ca.functions:
            functions.append((ca.path, fn.name))

    seen: set[tuple[str, str]] = set()
    ordered_keys: list[tuple[str, str]] = []
    for key in functions:
        if key not in seen:
            seen.add(key)
            ordered_keys.append(key)

    ordered = [name for _, name in ordered_keys]

    # Which functions have any mapped test?
    tested_functions = set(tests.function_to_tests.keys())

    # Which gap IDs were addressed by a generated test?
    addressed_gap_ids = {
        gt.targets_gap for gt in generated_tests if gt.targets_gap
    }

    # Which functions had at least one gap that a generated test targeted
    # AND execution_passed confirms those tests actually passed?
    # We conservatively only count a function's gap as addressed when
    # there is evidence of a passing run (execution_passed > 0).
    effectively_addressed_gap_ids: set[str] = set()
    if execution_passed > 0:
        effectively_addressed_gap_ids = addressed_gap_ids

    unaddressed_gap_functions: set[str] = set()
    for g in gaps:
        if g.id not in effectively_addressed_gap_ids:
            unaddressed_gap_functions.add(g.function)

    # Which functions had ALL their gaps addressed by passing generated tests?
    all_gap_functions: set[str] = {g.function for g in gaps}
    fully_addressed_functions: set[str] = set()
    for fn_name in all_gap_functions:
        fn_gaps = [g for g in gaps if g.function == fn_name]
        if all(g.id in effectively_addressed_gap_ids for g in fn_gaps):
            fully_addressed_functions.add(fn_name)

    verified = 0
    partial = 0
    unresolved = 0

    for _, name in ordered_keys:
        has_test = name in tested_functions
        has_unaddressed_gap = name in unaddressed_gap_functions

        if has_test and not has_unaddressed_gap:
            verified += 1
        elif has_test and has_unaddressed_gap:
            partial += 1
        elif not has_test and name in fully_addressed_functions:
            # No mapped test, but all gaps for this function were addressed
            # by generated tests that actually passed → treat as verified.
            verified += 1
        else:
            unresolved += 1

    return PathSummary(
        files_changed=diff.files_changed,
        functions_affected=len(ordered_keys),
        function_names=ordered,
        verified_paths=verified,
        partial_paths=partial,
        unresolved_paths=unresolved,
    )