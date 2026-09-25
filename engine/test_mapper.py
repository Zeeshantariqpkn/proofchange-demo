"""Test mapper.

Maps functions under analysis to the tests that reference them.
Works by parsing pytest-style test files with the AST and looking for
imports and call sites.
"""
from __future__ import annotations

import ast
import os
from typing import Iterable

from engine.models import MappedTest, TestMap


def _iter_test_files(root: str) -> Iterable[str]:
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if name.startswith("test_") and name.endswith(".py"):
                yield os.path.join(dirpath, name)
            elif name.endswith("_test.py"):
                yield os.path.join(dirpath, name)


def _referenced_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name):
                names.add(f.id)
            elif isinstance(f, ast.Attribute):
                names.add(f.attr)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


def map_tests(
    functions: list[str],
    tests_root: str,
) -> TestMap:
    """Build a TestMap for the given function names by scanning tests_root."""
    result = TestMap()
    if not os.path.isdir(tests_root):
        return result

    for path in _iter_test_files(tests_root):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                source = fh.read()
        except OSError:
            continue

        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        # Collect test functions and check what each one references.
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                referenced = _referenced_names(node)
                hits = [f for f in functions if f in referenced]
                if not hits:
                    continue
                mt = MappedTest(
                    test_name=node.name,
                    file=path,
                    references=hits,
                    docstring=ast.get_docstring(node) or "",
                )
                result.all_tests.append(mt)
                for h in hits:
                    result.function_to_tests.setdefault(h, []).append(mt)

    return result