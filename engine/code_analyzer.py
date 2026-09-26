"""AST-based Python code analyzer.

Extracts functions, classes, conditionals, branches and return paths
from Python source. Uses Python's ast module - no regex guessing.
"""
from __future__ import annotations

import ast
from typing import Optional

from engine.models import BranchInfo, CodeAnalysis, FunctionInfo


def _unparse(node: ast.AST) -> str:
    """Return a source string for an AST node, works on Python 3.8+."""
    try:
        return ast.unparse(node)
    except Exception:
        return ""


class _FunctionVisitor(ast.NodeVisitor):
    def __init__(self, path: str = "") -> None:
        self.functions: list[FunctionInfo] = []
        self.classes: list[str] = []
        self._path = path

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.classes.append(node.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def _visit_function(self, node) -> None:
        args = [a.arg for a in node.args.args]
        info = FunctionInfo(
            name=node.name,
            lineno=node.lineno,
            args=args,
            source_path=self._path,
        )

        for child in ast.walk(node):
            if isinstance(child, ast.If):
                info.branches.append(
                    BranchInfo(
                        expression=_unparse(child.test),
                        kind="if",
                        lineno=child.lineno,
                    )
                )
                if child.orelse:
                    orelse = child.orelse
                    if len(orelse) == 1 and isinstance(orelse[0], ast.If):
                        info.branches.append(
                            BranchInfo(
                                expression=_unparse(orelse[0].test),
                                kind="elif",
                                lineno=orelse[0].lineno,
                            )
                        )
                    else:
                        info.branches.append(
                            BranchInfo(
                                expression="default",
                                kind="else",
                                lineno=child.lineno,
                            )
                        )
            elif isinstance(child, ast.Return):
                info.return_paths += 1
            elif isinstance(child, ast.Call):
                func = child.func
                if isinstance(func, ast.Name):
                    info.calls.append(func.id)
                elif isinstance(func, ast.Attribute):
                    info.calls.append(func.attr)

        self.functions.append(info)

    def visit_Module(self, node: ast.Module) -> None:
        self.generic_visit(node)


def analyze_source(source: str, path: str = "<unknown>") -> CodeAnalysis:
    """Analyze Python source. Gracefully handles syntax errors."""
    analysis = CodeAnalysis(path=path)
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        analysis.parse_error = f"{exc.msg} (line {exc.lineno})"
        return analysis
    except Exception as exc:
        analysis.parse_error = f"{type(exc).__name__}: {exc}"
        return analysis

    visitor = _FunctionVisitor(path=path)
    visitor.visit(tree)
    analysis.functions = visitor.functions
    analysis.classes = visitor.classes
    return analysis


def analyze_file(path: str) -> CodeAnalysis:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            source = fh.read()
    except OSError as exc:
        return CodeAnalysis(path=path, parse_error=f"read error: {exc}")
    return analyze_source(source, path=path)