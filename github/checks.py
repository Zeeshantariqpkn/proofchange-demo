"""GitHub Check Run formatting.

Produces the human-readable summary shown in the PR check.
"""
from __future__ import annotations

from engine.models import EvidencePackage


def _conclusion_for(level: str) -> str:
    if level == "STRONG":
        return "success"
    if level == "PARTIAL":
        return "neutral"
    return "failure"


def format_check(pkg: EvidencePackage) -> dict:
    d = pkg.to_dict()
    change = d["change"]
    testing = d["testing"]
    execution = d["execution"]
    paths = d["paths"]
    evidence = d["evidence"]

    lines = [
        "PROOFCHANGE — Change Verification",
        "",
        f"Change: {pkg.pr_title or 'Code change'}",
        "",
        f"Files changed: {change['files_changed']}",
        f"Functions affected: {change['functions_affected']}",
        "",
        f"Test gaps: {testing['test_gaps']}",
        f"Generated tests: {testing['generated_tests']}",
        "",
        f"Verification: {execution['passed']} / {execution['tests_executed']} passed",
        "",
        f"Evidence: {evidence['level']}",
        "",
        "✔ Changed code mapped",
        "✔ Test gaps analyzed",
        "✔ Generated tests executed",
        "✔ Verification completed",
    ]
    if paths["unresolved"] > 0:
        lines.append("")
        lines.append(f"⚠ {paths['unresolved']} unresolved path(s)")

    summary = "\n".join(lines)

    return {
        "name": "ProofChange — Change Verification",
        "conclusion": _conclusion_for(evidence["level"]),
        "title": f"Evidence: {evidence['level']}",
        "summary": summary,
        "text": d.get("evidence", {}).get("rationale", ""),
    }