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
# Use a backreference so opening and closing quotes must match.
_LITERAL_RE = re.compile(r"""(['"])([^'"]+)\1""")


def _scenario_label(branch: BranchInfo) -> str:
    """Turn a branch expression into a human-readable scenario."""
    expr = branch.expression or "default"

    if branch.kind == "else":
        return "default / fallback"

    literals = _LITERAL_RE.findall(expr)
    if literals:
        # findall returns (quote_char, content) tuples due to the two groups.
        # e.g. customer_type == "vip"  ->  'vip' customer
        head = literals[0][1]
        return f"{head} scenario"

    # Fallback: use the raw expression
    return expr


_HIGH_SEVERITY_KEYWORDS = frozenset(
    ("auth", "admin", "permission", "token", "secret", "password", "role", "security")
)


def _branch_severity(branch: BranchInfo) -> str:
    expr_lower = (branch.expression or "").lower()
    if any(kw in expr_lower for kw in _HIGH_SEVERITY_KEYWORDS):
        return "high"
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

        # Emit a low-severity gap for functions with no tests and no branches.
        if not fn.branches:
            if not mapped:
                gaps.append(
                    TestGap(
                        id=_make_gap_id(counter),
                        function=fn.name,
                        scenario="no branch coverage",
                        reason=f"Function '{fn.name}' has no mapped automated test.",
                        severity="low",
                        suggested_test=f"test_{re.sub(r'[^a-z0-9]+', '_', fn.name.lower()).strip('_')}",
                    )
                )
                counter += 1
            continue

        for branch in fn.branches:
            label = _scenario_label(branch)
            expr_display = branch.expression or label

            # Skip the default branch if any mapped test seems to hit the
            # "no match" path (heuristic: test names mention default/else/regular).
            if branch.kind == "else":
                if any(k in " ".join(covered) for k in ("default", "else", "fallback", "regular", "none")):
                    continue

            # Does any mapped test mention this scenario?
            # Use the full label (not just the first word) to reduce false positives
            # on raw-expression labels like "customer_type == 'premium'".
            scenario_key = label.lower()
            # Also derive a short keyword: first word only when the label was
            # produced from a string literal (contains "scenario"), otherwise
            # use the whole label for matching.
            if "scenario" in scenario_key:
                match_key = label.split()[0].lower()
            else:
                match_key = scenario_key
            if not match_key:
                continue
            hit = any(match_key in c for c in covered)
            if hit:
                continue

            suggested = "test_" + re.sub(r"[^a-z0-9]+", "_", label.split()[0].lower()).strip("_")
            gaps.append(
                TestGap(
                    id=_make_gap_id(counter),
                    function=fn.name,
                    scenario=label,
                    reason=f"Branch '{expr_display}' has no mapped automated test.",
                    severity=_branch_severity(branch),
                    suggested_test=suggested,
                )
            )
            counter += 1

    return gaps