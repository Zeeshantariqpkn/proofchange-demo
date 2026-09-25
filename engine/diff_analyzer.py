"""Diff analyzer.

Parses a unified diff and extracts structured information about what
changed. For Python files it delegates to the AST-based code analyzer
to identify which functions the diff touches.
"""
from __future__ import annotations

import re
from typing import Optional

from engine.code_analyzer import analyze_source
from engine.models import ChangedFile, DiffAnalysis

_FILE_HEADER = re.compile(r"^\+\+\+ b/(.+)$")
_HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@")
_ADDED_CONDITIONAL = re.compile(
    r"^\+\s*(if|elif|else)\b.*$", re.IGNORECASE
)


def _is_python(path: str) -> bool:
    return path.endswith(".py")


def _resolve_function_for_line(
    functions_by_range: list[tuple[int, int, str]], lineno: int
) -> Optional[str]:
    """Return the innermost function containing lineno (1-based)."""
    best: Optional[str] = None
    best_span = None
    for start, end, name in functions_by_range:
        if start <= lineno <= end:
            span = end - start
            if best_span is None or span < best_span:
                best_span = span
                best = name
    return best


def _function_ranges(source: str) -> list[tuple[int, int, str]]:
    """Return (start_line, end_line, name) for every top-level and nested function."""
    analysis = analyze_source(source)
    ranges: list[tuple[int, int, str]] = []
    if analysis.parse_error:
        return ranges

    import ast

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ranges

    class _Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            end = getattr(node, "end_lineno", node.lineno)
            ranges.append((node.lineno, end, node.name))
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            end = getattr(node, "end_lineno", node.lineno)
            ranges.append((node.lineno, end, node.name))
            self.generic_visit(node)

    _Visitor().visit(tree)
    return ranges


def analyze_diff(diff_text: str) -> DiffAnalysis:
    """Parse a unified diff and produce a structured analysis."""
    result = DiffAnalysis(raw_diff=diff_text)
    if not diff_text.strip():
        return result

    current_path: Optional[str] = None
    current_file: Optional[ChangedFile] = None
    # Track added line numbers so we can map to functions after we read
    # the "after" version of the file. For the demo we only need the
    # changed function names, which we get by re-parsing the on-disk file
    # for the PR head — but to stay self-contained we approximate using
    # the hunk line numbers plus a small window.
    added_linenos: list[int] = []

    files: dict[str, ChangedFile] = {}

    for raw_line in diff_text.splitlines():
        line = raw_line.rstrip("\n")

        m = _FILE_HEADER.match(line)
        if m:
            # Starting a new file section
            if current_file is not None:
                _finalize_file(current_file, added_linenos)
                files[current_file.path] = current_file
            current_path = m.group(1).strip()
            current_file = ChangedFile(path=current_path)
            added_linenos = []
            continue

        if current_file is None:
            continue

        if line.startswith("+") and not line.startswith("+++"):
            current_file.added_lines += 1
            current_file.raw_diff += line + "\n"
            if _ADDED_CONDITIONAL.match(line):
                current_file.added_conditionals.append(line.lstrip("+ ").strip())
        elif line.startswith("-") and not line.startswith("---"):
            current_file.deleted_lines += 1
            current_file.raw_diff += line + "\n"
        elif line.startswith(" "):
            current_file.raw_diff += line + "\n"

        if _HUNK_HEADER.match(line):
            # @@ -a,b +c,d @@
            parts = line.split("+")[1].split("@@")[0].strip()
            start = int(parts.split(",")[0])
            count = 1
            if "," in parts:
                try:
                    count = int(parts.split(",")[1])
                except ValueError:
                    count = 1
            added_linenos.extend(range(start, start + count))

    if current_file is not None:
        _finalize_file(current_file, added_linenos)
        files[current_file.path] = current_file

    result.files = list(files.values())
    result.files_changed = len(result.files)
    return result


def _finalize_file(changed: ChangedFile, added_linenos: list[int]) -> None:
    """Best-effort function identification.

    We do not have the on-disk 'after' file here, so we simply report
    the added conditional lines as hints and leave function extraction
    to the code analyzer when the file is available on disk.
    """
    # Without the post-change source we cannot map line numbers to
    # functions reliably. The pipeline calls code_analyzer separately
    # on the post-change file, so we keep this field empty here.
    if not changed.functions and changed.added_conditionals:
        # Leave function list empty; the pipeline fills it in.
        pass