"""Structured data models used across the ProofChange engine.

These are plain dataclasses / Pydantic models so they can be serialized
directly into the Change Evidence Package JSON.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ChangedFile:
    path: str
    added_lines: int = 0
    deleted_lines: int = 0
    modified_lines: int = 0
    functions: list[str] = field(default_factory=list)
    added_conditionals: list[str] = field(default_factory=list)
    raw_diff: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DiffAnalysis:
    files_changed: int = 0
    files: list[ChangedFile] = field(default_factory=list)
    raw_diff: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["files"] = [f.to_dict() for f in self.files]
        return d


@dataclass
class BranchInfo:
    expression: str
    kind: str = "if"  # if / elif / else / default
    lineno: int = 0


@dataclass
class FunctionInfo:
    name: str
    lineno: int
    args: list[str] = field(default_factory=list)
    branches: list[BranchInfo] = field(default_factory=list)
    return_paths: int = 0
    calls: list[str] = field(default_factory=list)
    is_class: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "lineno": self.lineno,
            "args": self.args,
            "branches": [asdict(b) for b in self.branches],
            "return_paths": self.return_paths,
            "calls": self.calls,
        }


@dataclass
class CodeAnalysis:
    path: str
    functions: list[FunctionInfo] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    parse_error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "classes": self.classes,
            "parse_error": self.parse_error,
            "functions": [f.to_dict() for f in self.functions],
        }


@dataclass
class MappedTest:
    test_name: str
    file: str
    references: list[str] = field(default_factory=list)
    docstring: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TestMap:
    function_to_tests: dict[str, list[MappedTest]] = field(default_factory=dict)
    all_tests: list[MappedTest] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "function_to_tests": {
                k: [t.to_dict() for t in v]
                for k, v in self.function_to_tests.items()
            },
            "all_tests": [t.to_dict() for t in self.all_tests],
        }


@dataclass
class TestGap:
    id: str
    function: str
    scenario: str
    reason: str
    severity: str  # low / medium / high
    suggested_test: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GeneratedTest:
    test_name: str
    file: str
    code: str
    targets_gap: str = ""
    source: str = "bob-assisted"  # bob-assisted / runtime_llm / manual

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionResult:
    exit_code: int = 0
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration_s: float = 0.0
    stdout: str = ""
    stderr: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvidencePackage:
    id: str
    created_at: str
    repository: str = "demo_repo"
    commit: str = ""
    pr_number: Optional[int] = None
    pr_title: str = ""
    change: dict[str, Any] = field(default_factory=dict)
    testing: dict[str, Any] = field(default_factory=dict)
    execution: dict[str, Any] = field(default_factory=dict)
    paths: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, Any] = field(default_factory=dict)
    ai_mode: str = "documented_bob_workflow"
    ai_assisted_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)