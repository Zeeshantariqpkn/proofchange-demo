"""Tests for engine/evidence.py and engine/impact_analyzer.py.

Focuses on the STRONG/PARTIAL/INSUFFICIENT classification rules for the
canonical VIP-discount scenario:

  pricing.py adds a `vip` branch → 1 gap detected (GAP-001) →
  test_generator emits test_vip (targets GAP-001) →
  3 tests run (premium, regular, vip) → all pass → STRONG evidence.
"""
from __future__ import annotations

import textwrap

import pytest

from engine.evidence import _compute_level
from engine.impact_analyzer import summarize_impact
from engine.models import (
    BranchInfo,
    CodeAnalysis,
    DiffAnalysis,
    ExecutionResult,
    FunctionInfo,
    GeneratedTest,
    MappedTest,
    TestGap,
    TestMap,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _exec(total: int = 3, passed: int = 3, failed: int = 0) -> ExecutionResult:
    return ExecutionResult(
        exit_code=0,
        total=total,
        passed=passed,
        failed=failed,
        skipped=0,
        duration_s=0.05,
    )


def _vip_gap() -> TestGap:
    return TestGap(
        id="GAP-001",
        function="calculate_discount",
        scenario="vip scenario",
        reason="Branch 'customer_type == \"vip\"' has no mapped automated test.",
        severity="medium",
        suggested_test="test_vip",
    )


def _vip_generated() -> GeneratedTest:
    return GeneratedTest(
        test_name="test_vip",
        file="demo_repo/tests/test_generated.py",
        code='def test_vip_discount():\n    assert calculate_discount(100, "vip") == 70\n',
        targets_gap="GAP-001",
        source="bob-assisted",
    )


def _discount_fn() -> FunctionInfo:
    """The post-change calculate_discount with premium + vip branches."""
    return FunctionInfo(
        name="calculate_discount",
        lineno=4,
        args=["price", "customer_type"],
        branches=[
            BranchInfo(expression='customer_type == "premium"', kind="if"),
            BranchInfo(expression='customer_type == "vip"', kind="if"),
        ],
        return_paths=3,
        source_path="src/pricing.py",
    )


def _premium_test_map() -> TestMap:
    """TestMap with test_premium_discount and test_regular_price mapped to calculate_discount."""
    mt_premium = MappedTest(
        test_name="test_premium_discount",
        file="demo_repo/tests/test_pricing.py",
        references=["calculate_discount"],
    )
    mt_regular = MappedTest(
        test_name="test_regular_price",
        file="demo_repo/tests/test_pricing.py",
        references=["calculate_discount"],
    )
    tm = TestMap(
        function_to_tests={"calculate_discount": [mt_premium, mt_regular]},
        all_tests=[mt_premium, mt_regular],
    )
    return tm


def _diff() -> DiffAnalysis:
    from engine.models import ChangedFile
    return DiffAnalysis(
        files_changed=1,
        files=[
            ChangedFile(
                path="src/pricing.py",
                added_lines=3,
                functions=["calculate_discount"],
            )
        ],
    )


# ---------------------------------------------------------------------------
# _compute_level tests
# ---------------------------------------------------------------------------

class TestComputeLevel:
    """Unit tests for the evidence._compute_level function."""

    def test_strong_vip_scenario(self):
        """VIP gap addressed by generated test + all tests pass → STRONG."""
        level, rationale = _compute_level(
            gaps=[_vip_gap()],
            generated_tests=[_vip_generated()],
            execution=_exec(total=3, passed=3, failed=0),
            analyzed_paths=1,
            verified_paths=1,
        )
        assert level == "STRONG", f"Expected STRONG, got {level!r}. Rationale: {rationale}"

    def test_insufficient_when_no_tests_executed(self):
        """Zero tests executed → INSUFFICIENT regardless of gaps."""
        level, _ = _compute_level(
            gaps=[_vip_gap()],
            generated_tests=[_vip_generated()],
            execution=_exec(total=0, passed=0, failed=0),
            analyzed_paths=1,
            verified_paths=1,
        )
        assert level == "INSUFFICIENT"

    def test_insufficient_when_test_fails(self):
        """Any failing test → INSUFFICIENT."""
        level, _ = _compute_level(
            gaps=[_vip_gap()],
            generated_tests=[_vip_generated()],
            execution=_exec(total=3, passed=2, failed=1),
            analyzed_paths=1,
            verified_paths=1,
        )
        assert level == "INSUFFICIENT"

    def test_partial_when_gap_unaddressed(self):
        """Gap exists but no generated test targets it → PARTIAL."""
        level, _ = _compute_level(
            gaps=[_vip_gap()],
            generated_tests=[],  # nothing targets GAP-001
            execution=_exec(total=2, passed=2, failed=0),
            analyzed_paths=1,
            verified_paths=0,
        )
        assert level == "PARTIAL"

    def test_partial_when_ratio_below_threshold(self):
        """Even with all gaps addressed, low verified ratio → PARTIAL."""
        level, _ = _compute_level(
            gaps=[_vip_gap()],
            generated_tests=[_vip_generated()],
            execution=_exec(total=3, passed=3, failed=0),
            analyzed_paths=10,  # 10 functions
            verified_paths=6,   # only 60% verified < 70%
        )
        assert level == "PARTIAL"

    def test_strong_with_addressed_high_severity_gap(self):
        """A high-severity gap addressed by a passing generated test → STRONG (not PARTIAL)."""
        high_gap = TestGap(
            id="GAP-002",
            function="login",
            scenario="admin scenario",
            reason="Branch with 'admin' keyword.",
            severity="high",
            suggested_test="test_admin",
        )
        gen = GeneratedTest(
            test_name="test_admin",
            file="tests/test_generated.py",
            code="def test_admin(): pass",
            targets_gap="GAP-002",
            source="bob-assisted",
        )
        level, rationale = _compute_level(
            gaps=[high_gap],
            generated_tests=[gen],
            execution=_exec(total=1, passed=1, failed=0),
            analyzed_paths=1,
            verified_paths=1,
        )
        assert level == "STRONG", f"Expected STRONG, got {level!r}. Rationale: {rationale}"

    def test_partial_when_high_severity_gap_unaddressed(self):
        """Unaddressed high-severity gap always → PARTIAL."""
        high_gap = TestGap(
            id="GAP-002",
            function="login",
            scenario="admin scenario",
            reason="Branch with 'admin' keyword.",
            severity="high",
            suggested_test="test_admin",
        )
        level, rationale = _compute_level(
            gaps=[high_gap],
            generated_tests=[],  # not addressed
            execution=_exec(total=2, passed=2, failed=0),
            analyzed_paths=1,
            verified_paths=1,
        )
        assert level == "PARTIAL"
        assert "high-severity" in rationale


# ---------------------------------------------------------------------------
# summarize_impact integration with _compute_level
# ---------------------------------------------------------------------------

class TestVipScenarioEndToEnd:
    """Full impact → evidence pipeline for the VIP-discount scenario."""

    def test_impact_verified_paths(self):
        """calculate_discount counts as verified when VIP gap is addressed by passing test."""
        impact = summarize_impact(
            diff=_diff(),
            code=[CodeAnalysis(path="src/pricing.py", functions=[_discount_fn()])],
            tests=_premium_test_map(),
            gaps=[_vip_gap()],
            generated_tests=[_vip_generated()],
            execution_passed=3,
        )
        assert impact.functions_affected == 1
        assert impact.verified_paths == 1
        assert impact.partial_paths == 0
        assert impact.unresolved_paths == 0

    def test_full_pipeline_produces_strong(self):
        """End-to-end: impact summary fed into _compute_level → STRONG."""
        impact = summarize_impact(
            diff=_diff(),
            code=[CodeAnalysis(path="src/pricing.py", functions=[_discount_fn()])],
            tests=_premium_test_map(),
            gaps=[_vip_gap()],
            generated_tests=[_vip_generated()],
            execution_passed=3,
        )
        level, rationale = _compute_level(
            gaps=[_vip_gap()],
            generated_tests=[_vip_generated()],
            execution=_exec(total=3, passed=3, failed=0),
            analyzed_paths=impact.functions_affected,
            verified_paths=impact.verified_paths,
        )
        assert level == "STRONG", f"Expected STRONG, got {level!r}. Rationale: {rationale}"
        assert "1 gap(s) addressed" in rationale
        assert "1/1" in rationale

    def test_impact_partial_when_execution_zero(self):
        """Without a passing execution, the VIP gap is not effectively addressed."""
        impact = summarize_impact(
            diff=_diff(),
            code=[CodeAnalysis(path="src/pricing.py", functions=[_discount_fn()])],
            tests=_premium_test_map(),
            gaps=[_vip_gap()],
            generated_tests=[_vip_generated()],
            execution_passed=0,  # no passing tests yet
        )
        # has_test=True (premium tests mapped), has_unaddressed_gap=True (vip not confirmed)
        assert impact.partial_paths == 1
        assert impact.verified_paths == 0
