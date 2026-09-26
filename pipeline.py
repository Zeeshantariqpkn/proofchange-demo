"""ProofChange analysis pipeline.

Ties together diff analysis, code analysis, test mapping, gap
detection, test generation, execution, and evidence packaging.

This is the single source of truth used by both the Streamlit UI and
the FastAPI endpoints.
"""
from __future__ import annotations

import os
from typing import Any, Optional

from ai.bob_adapter import BobAdapter
from ai.test_generator import generate_tests, write_generated_tests
from engine import diff_analyzer, evidence as evidence_engine
from engine.code_analyzer import analyze_file, analyze_source
from engine.gap_detector import detect_gaps
from engine.impact_analyzer import summarize_impact
from engine.models import (
    CodeAnalysis,
    EvidencePackage,
    ExecutionResult,
    TestMap,
)
from engine.runner import run_pytest
from engine.test_mapper import map_tests


_HERE = os.path.dirname(os.path.abspath(__file__))
DEMO_ROOT = os.path.join(_HERE, "demo_repo")
DEMO_SRC = os.path.join(DEMO_ROOT, "src")
DEMO_TESTS = os.path.join(DEMO_ROOT, "tests")
DEMO_PRICING = os.path.join(DEMO_SRC, "pricing.py")


_DEFAULT_DIFF = '''diff --git a/src/pricing.py b/src/pricing.py
--- a/src/pricing.py
+++ b/src/pricing.py
@@ -1,8 +1,12 @@
 """Pricing rules for the demo repository."""
 
 
 def calculate_discount(price, customer_type):
     if customer_type == "premium":
         return price * 0.80
 
+    if customer_type == "vip":
+        return price * 0.70
+
     return price
'''


def _load_demo_diff() -> str:
    diff_path = os.path.join(DEMO_ROOT, "change.diff")
    if os.path.exists(diff_path):
        with open(diff_path, "r", encoding="utf-8") as fh:
            return fh.read()
    return _DEFAULT_DIFF


def _post_change_source() -> str:
    with open(DEMO_PRICING, "r", encoding="utf-8") as fh:
        return fh.read()


def run_demo_pipeline(
    *,
    repository: str = "demo_repo",
    commit: str = "demo",
    pr_number: Optional[int] = None,
    pr_title: str = "Add VIP discount support",
    data_dir: str = "./data",
    cleanup_generated: bool = True,
) -> EvidencePackage:
    """Run the full pipeline against the bundled demo repo."""

    # 1. Diff analysis
    diff_text = _load_demo_diff()
    diff = diff_analyzer.analyze_diff(diff_text)

    # 2. Code analysis on the post-change source
    source = _post_change_source()
    code_analysis = analyze_source(source, path="src/pricing.py")

    # Fill in changed functions on the diff record from the AST.
    for f in diff.files:
        if f.path.endswith("pricing.py"):
            f.functions = [fn.name for fn in code_analysis.functions]

    # 3. Test mapping
    tests: TestMap = map_tests(
        functions=[fn.name for fn in code_analysis.functions],
        tests_root=DEMO_TESTS,
    )

    # 4. Gap detection
    gaps = detect_gaps(code_analysis.functions, tests)

    # 5. Test generation (Bob-assisted)
    adapter = BobAdapter()
    generated = generate_tests(
        gaps=gaps,
        functions=code_analysis.functions,
        adapter=adapter,
        tests_root=DEMO_TESTS,
    )

    written: list[str] = []
    if generated:
        written = write_generated_tests(generated)

    # 6. Execution (real pytest)
    execution = run_pytest(DEMO_ROOT)

    # 7. Impact summary
    impact = summarize_impact(
        diff,
        [code_analysis],
        tests,
        gaps,
        generated_tests=generated,
        execution_passed=execution.passed,
    )

    # 8. Evidence package
    pkg = evidence_engine.build_package(
        diff=diff,
        code_analyses=[code_analysis],
        tests=tests,
        gaps=gaps,
        generated_tests=generated,
        execution=execution,
        impact=impact,
        repository=repository,
        commit=commit,
        pr_number=pr_number,
        pr_title=pr_title,
        ai_mode=adapter.mode,
    )

    evidence_engine.save_package(pkg, data_dir)

    # 9. Cleanup generated test so the demo is reproducible.
    if cleanup_generated:
        for path in written:
            try:
                os.remove(path)
            except OSError:
                pass

    return pkg


def analyze_custom_diff(
    diff_text: str,
    *,
    repository: str = "custom",
    commit: str = "",
    pr_number: Optional[int] = None,
    pr_title: str = "",
    source_root: str = "",
    tests_root: str = "",
    repo_root: str = "",
    data_dir: str = "./data",
) -> EvidencePackage:
    """Analyze an arbitrary diff. Requires on-disk source and tests.

    repo_root is the directory where pytest should run (usually the
    repo's root, which contains tests/ and pytest.ini). If not given,
    it's inferred as the parent of source_root.
    """
    diff = diff_analyzer.analyze_diff(diff_text)

    code_analyses: list[CodeAnalysis] = []
    for f in diff.files:
        if source_root and f.path.endswith(".py"):
            candidate = os.path.join(source_root, os.path.basename(f.path))
            if os.path.exists(candidate):
                ca = analyze_file(candidate)
                f.functions = [fn.name for fn in ca.functions]
                code_analyses.append(ca)

    functions = [fn.name for ca in code_analyses for fn in ca.functions]
    tests = map_tests(functions=functions, tests_root=tests_root) if tests_root else TestMap()
    gaps = detect_gaps([fn for ca in code_analyses for fn in ca.functions], tests)

    adapter = BobAdapter()
    generated = generate_tests(
        gaps=gaps,
        functions=[fn for ca in code_analyses for fn in ca.functions],
        adapter=adapter,
        tests_root=tests_root or "./tests",
    )

    # Determine where to run pytest: explicit repo_root wins, else
    # fall back to source_root's parent.
    if repo_root:
        pytest_dir = repo_root
    elif source_root:
        pytest_dir = os.path.dirname(os.path.abspath(source_root))
    else:
        pytest_dir = "."

    execution = run_pytest(pytest_dir) if os.path.isdir(pytest_dir) else ExecutionResult()

    impact = summarize_impact(
        diff,
        code_analyses,
        tests,
        gaps,
        generated_tests=generated,
        execution_passed=execution.passed,
    )
    pkg = evidence_engine.build_package(
        diff=diff,
        code_analyses=code_analyses,
        tests=tests,
        gaps=gaps,
        generated_tests=generated,
        execution=execution,
        impact=impact,
        repository=repository,
        commit=commit,
        pr_number=pr_number,
        pr_title=pr_title,
        ai_mode=adapter.mode,
    )
    evidence_engine.save_package(pkg, data_dir)
    return pkg