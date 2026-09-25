"""Test-gap detector.

Compares inferred scenarios from the code change against the tests
that were mapped. Produces a list of TestGap records.

This is intentionally conservative: it flags *meaningful* missing
scenarios, not every possible branch combination.
"""
from __future__ import annotations

import re
from typing import Iterable

from engine.models import BranchInfo, FunctionInfo, TestGap, TestMap

# Common literal patterns we can extract as scenario descriptions.
_LITERAL_RE = re.compile(r"""['"]([^'"]+)['"]""")


def _scenario_label(branch: BranchInfo) -> str:
    """Turn a branch expression into a human-readable scenario."""
    expr = branch.expression or "default"

    if branch.kind == "else":
        return "default / fallback"

    literals = _LITERAL_RE.findall(expr)
    if literals:
        # e.g. customer_type == "vip"  ->  'vip' customer
        head = literals[0]
        return f"{head} scenario"

    # Fallback: use the raw expression
    return expr


def _branch_severity(branch: BranchInfo) -> str:
    if branch.kind in ("if", "elif"):
        return "medium"
    return "low"


def _make_gap_id(index: int) -> str:
    return f"GAP-{index:03d}"


def detect_gaps(
    functions: list[FunctionInfo],
    tests: TestMap,
) -> list[TestGap]:
    """Return gaps found by comparing branch scenarios to mapped tests."""
    gaps: list[TestGap] = []
    counter = 1

    for fn in functions:
        mapped = tests.function_to_tests.get(fn.name, [])
        # Build a set of "covered scenario strings" from mapped tests.
        covered: set[str] = set()
        for mt in mapped:
            # Cheap heuristic: test names and docstrings mention scenarios.
            covered.add(mt.test_name.lower())
            if mt.docstring:
                covered.add(mt.docstring.lower())

        for branch in fn.branches:
            label = _scenario_label(branch)
            # Skip the default branch if any mapped test seems to hit the
            # "no match" path (heuristic: test names mention default/else/regular).
            if branch.kind == "else":
                if any(k in " ".join(covered) for k in ("default", "else", "fallback", "regular", "none")):
                    continue

            # Does any mapped test mention this scenario?
            scenario_key = label.split()[0].lower()
            if not scenario_key:
                continue
            hit = any(scenario_key in c for c in covered)
            if hit:
                continue

            suggested = "test_" + re.sub(r"[^a-z0-9]+", "_", scenario_key).strip("_")
            gaps.append(
                TestGap(
                    id=_make_gap_id(counter),
                    function=fn.name,
                    scenario=label,
                    reason=f"Branch '{branch.expression}' has no mapped automated test.",
                    severity=_branch_severity(branch),
                    suggested_test=suggested,
                )
            )
            counter += 1

    return gaps