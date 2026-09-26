"""Tests for engine.evidence.simulate_with_generated_tests.

Verifies that the gap simulator returns the correct projected evidence
level for a variety of before/after scenarios without touching the
filesystem or spawning any subprocess.
"""
from __future__ import annotations

import uuid

import pytest

from engine.evidence import build_package, simulate_with_generated_tests
from engine.impact_analyzer import summarize_impact
from engine.models import (
    BranchInfo,
    ChangedFile,
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
# Shared fixtures
# ---------------------------------------------------------------------------

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
        code='from src.pricing import calculate_discount\n\ndef test_vip_discount():\n    assert calculate_discount(100, "vip") == 70\n',
        targets_gap="GAP-001",
        source="bob-assisted",
    )


def _discount_fn() -> FunctionInfo:
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


def _build_pkg(
    *,
    gaps: list[TestGap],
    generated: list[GeneratedTest],
    execution: ExecutionResult,
    verified_paths: int = 1,
):
    """Build a minimal EvidencePackage for simulation tests."""
    diff = DiffAnalysis(
        files_changed=1,
        files=[ChangedFile(path="src/pricing.py", added_lines=3, functions=["calculate_discount"])],
    )
    code = CodeAnalysis(path="src/pricing.py", functions=[_discount_fn()])
    mt_premium = MappedTest(
        test_name="test_premium_discount",
        file="demo_repo/tests/test_pricing.py",
        references=["calculate_discount"],
    )
    tests = TestMap(
        function_to_tests={"calculate_discount": [mt_premium]},
        all_tests=[mt_premium],
    )
    impact = summarize_impact(
        diff=diff,
        code=[code],
        tests=tests,
        gaps=gaps,
        generated_tests=generated,
        execution_passed=execution.passed,
    )
    return build_package(
        diff=diff,
        code_analyses=[code],
        tests=tests,
        gaps=gaps,
        generated_tests=generated,
        execution=execution,
        impact=impact,
    )


# ---------------------------------------------------------------------------
# simulate_with_generated_tests
# ---------------------------------------------------------------------------

class TestSimulateWithGeneratedTests:
    """Unit tests for the gap simulator helper."""

    def test_partial_becomes_strong_after_addressing_gap(self):
        """A package at PARTIAL with one unaddressed gap should project to
        STRONG when that gap's generated test is provided."""
        pkg = _build_pkg(
            gaps=[_vip_gap()],
            generated=[],                   # gap is NOT yet addressed
            execution=ExecutionResult(
                exit_code=0, total=2, passed=2, failed=0, skipped=0, duration_s=0.1
            ),
            verified_paths=0,
        )
        assert pkg.to_dict()["evidence"]["level"] == "PARTIAL"

        level, rationale = simulate_with_generated_tests(pkg, [_vip_generated()])

        assert level == "STRONG", f"Expected STRONG, got {level!r}. Rationale: {rationale}"
        assert "addressed" in rationale.lower() or "passed" in rationale.lower()

    def test_strong_remains_strong(self):
        """Adding another test to an already-STRONG package keeps it STRONG."""
        pkg = _build_pkg(
            gaps=[_vip_gap()],
            generated=[_vip_generated()],   # gap already addressed
            execution=ExecutionResult(
                exit_code=0, total=3, passed=3, failed=0, skipped=0, duration_s=0.1
            ),
            verified_paths=1,
        )
        assert pkg.to_dict()["evidence"]["level"] == "STRONG"

        extra = GeneratedTest(
            test_name="test_extra",
            file="demo_repo/tests/test_generated.py",
            code="def test_extra(): pass",
            targets_gap="GAP-001",
            source="bob-assisted",
        )
        level, _ = simulate_with_generated_tests(pkg, [extra])
        assert level == "STRONG"

    def test_insufficient_stays_insufficient_when_tests_fail(self):
        """If the existing execution has failures the simulation must not
        project an optimistic level even with additional tests supplied."""
        pkg = _build_pkg(
            gaps=[_vip_gap()],
            generated=[],
            execution=ExecutionResult(
                exit_code=1, total=3, passed=2, failed=1, skipped=0, duration_s=0.1
            ),
            verified_paths=0,
        )
        assert pkg.to_dict()["evidence"]["level"] == "INSUFFICIENT"

        level, rationale = simulate_with_generated_tests(pkg, [_vip_generated()])

        # A failing test means the simulated execution still has failed > 0.
        assert level == "INSUFFICIENT"
        assert "failed" in rationale.lower()

    def test_empty_additional_tests_returns_same_level(self):
        """Passing an empty list must produce the same level as the current package."""
        pkg = _build_pkg(
            gaps=[_vip_gap()],
            generated=[],
            execution=ExecutionResult(
                exit_code=0, total=2, passed=2, failed=0, skipped=0, duration_s=0.1
            ),
            verified_paths=0,
        )
        current_level = pkg.to_dict()["evidence"]["level"]
        sim_level, _ = simulate_with_generated_tests(pkg, [])
        assert sim_level == current_level

    def test_return_type_is_tuple_of_two_strings(self):
        """simulate_with_generated_tests must return (str, str)."""
        pkg = _build_pkg(
            gaps=[_vip_gap()],
            generated=[],
            execution=ExecutionResult(
                exit_code=0, total=1, passed=1, failed=0, skipped=0, duration_s=0.05
            ),
            verified_paths=0,
        )
        result = simulate_with_generated_tests(pkg, [_vip_generated()])
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(isinstance(s, str) for s in result)
