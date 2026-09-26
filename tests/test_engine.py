"""Pytest test suite for engine/code_analyzer.py and engine/gap_detector.py."""
from __future__ import annotations

import textwrap

import pytest

from engine.code_analyzer import analyze_source, analyze_file
from engine.gap_detector import detect_gaps
from engine.models import BranchInfo, FunctionInfo, MappedTest, TestMap


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_test_map(**kwargs: list[MappedTest]) -> TestMap:
    """Build a TestMap from keyword args mapping function name -> list[MappedTest]."""
    return TestMap(function_to_tests=dict(kwargs))


def _mapped(name: str, docstring: str = "") -> MappedTest:
    return MappedTest(test_name=name, file="test_x.py", docstring=docstring)


# ===========================================================================
# engine/code_analyzer.py — analyze_source
# ===========================================================================


class TestAnalyzeSourceHappyPath:
    """Normal, valid Python inputs."""

    def test_simple_function_detected(self):
        """A plain function is extracted with correct name, lineno and args."""
        src = textwrap.dedent("""\
            def greet(name, greeting):
                return greeting + " " + name
        """)
        result = analyze_source(src)
        assert result.parse_error is None
        assert len(result.functions) == 1
        fn = result.functions[0]
        assert fn.name == "greet"
        assert fn.lineno == 1
        assert fn.args == ["name", "greeting"]
        assert fn.return_paths == 1

    def test_function_with_if_elif_else_branches(self):
        """if / elif / else branches are all captured."""
        src = textwrap.dedent("""\
            def classify(x):
                if x > 100:
                    return "big"
                elif x > 10:
                    return "medium"
                else:
                    return "small"
        """)
        result = analyze_source(src)
        assert result.parse_error is None
        fn = result.functions[0]
        kinds = [b.kind for b in fn.branches]
        assert "if" in kinds
        assert "elif" in kinds
        assert "else" in kinds

    def test_class_name_collected(self):
        """Class names appear in analysis.classes."""
        src = textwrap.dedent("""\
            class MyService:
                def run(self):
                    pass
        """)
        result = analyze_source(src)
        assert result.parse_error is None
        assert "MyService" in result.classes

    def test_method_inside_class_collected(self):
        """Methods inside a class are included in analysis.functions."""
        src = textwrap.dedent("""\
            class Calculator:
                def add(self, a, b):
                    return a + b
        """)
        result = analyze_source(src)
        fn_names = [f.name for f in result.functions]
        assert "add" in fn_names

    def test_calls_are_recorded(self):
        """Function calls inside a function body appear in fn.calls."""
        src = textwrap.dedent("""\
            def process(data):
                cleaned = strip(data)
                result = validate(cleaned)
                return result
        """)
        result = analyze_source(src)
        fn = result.functions[0]
        assert "strip" in fn.calls
        assert "validate" in fn.calls

    def test_async_function_detected(self):
        """async def functions are detected the same as regular ones."""
        src = textwrap.dedent("""\
            async def fetch(url):
                return await get(url)
        """)
        result = analyze_source(src)
        assert result.parse_error is None
        assert len(result.functions) == 1
        assert result.functions[0].name == "fetch"

    def test_multiple_functions(self):
        """Multiple top-level functions are all captured."""
        src = textwrap.dedent("""\
            def alpha():
                pass

            def beta():
                pass

            def gamma():
                pass
        """)
        result = analyze_source(src)
        names = [f.name for f in result.functions]
        assert names == ["alpha", "beta", "gamma"]

    def test_custom_path_stored(self):
        """The `path` argument is forwarded into the CodeAnalysis object."""
        result = analyze_source("x = 1", path="mymodule/utils.py")
        assert result.path == "mymodule/utils.py"


class TestAnalyzeSourceEdgeCases:
    """Boundary and unusual inputs."""

    def test_empty_source(self):
        """Empty string produces no functions, no error."""
        result = analyze_source("")
        assert result.parse_error is None
        assert result.functions == []
        assert result.classes == []

    def test_whitespace_only_source(self):
        """Whitespace-only string is valid Python and produces no functions."""
        result = analyze_source("   \n\t\n   ")
        assert result.parse_error is None
        assert result.functions == []

    def test_single_line_function(self):
        """One-liner lambda-style function on a single source line."""
        result = analyze_source("def noop(): pass")
        assert result.parse_error is None
        assert len(result.functions) == 1
        assert result.functions[0].name == "noop"

    def test_nested_functions(self):
        """The outer function is always collected.
        
        The visitor does not recurse into nested FunctionDef bodies
        (no generic_visit call inside _visit_function), so only the
        outermost function appears in results.  This test documents
        that actual behaviour.
        """
        src = textwrap.dedent("""\
            def outer(x):
                def inner(y):
                    return y * 2
                return inner(x)
        """)
        result = analyze_source(src)
        fn_names = [f.name for f in result.functions]
        assert "outer" in fn_names
        # inner is not visited because _visit_function does not call
        # generic_visit; the visitor descends only via ast.walk for
        # branch/return/call extraction, not for nested function discovery.
        assert "inner" not in fn_names

    def test_function_no_args(self):
        """A function with no parameters has an empty args list."""
        src = "def ping():\n    return True\n"
        result = analyze_source(src)
        assert result.functions[0].args == []

    def test_no_branches_function(self):
        """A function with no conditionals has an empty branches list."""
        src = textwrap.dedent("""\
            def simple(a, b):
                return a + b
        """)
        result = analyze_source(src)
        assert result.functions[0].branches == []


class TestAnalyzeSourceSyntaxError:
    """Graceful handling of bad Python input."""

    def test_syntax_error_sets_parse_error(self):
        """SyntaxError in source sets parse_error and returns empty lists."""
        bad = "def broken(:\n    pass\n"
        result = analyze_source(bad)
        assert result.parse_error is not None
        assert result.functions == []
        assert result.classes == []

    def test_syntax_error_message_contains_line(self):
        """The parse_error string includes a line-number reference."""
        bad = "def f(\n"  # unclosed paren
        result = analyze_source(bad)
        assert result.parse_error is not None
        # ast reports 'line <N>' in the message built by analyze_source
        assert "line" in result.parse_error.lower()


class TestAnalyzeFile:
    """analyze_file reads from disk; test missing-file handling."""

    def test_missing_file_returns_read_error(self, tmp_path):
        """A nonexistent path sets parse_error with 'read error'."""
        result = analyze_file(str(tmp_path / "does_not_exist.py"))
        assert result.parse_error is not None
        assert "read error" in result.parse_error.lower()

    def test_real_file_analyzed(self, tmp_path):
        """A real file on disk is parsed correctly via analyze_file."""
        src = "def hello():\n    return 'world'\n"
        p = tmp_path / "sample.py"
        p.write_text(src, encoding="utf-8")
        result = analyze_file(str(p))
        assert result.parse_error is None
        assert len(result.functions) == 1
        assert result.functions[0].name == "hello"


# ===========================================================================
# engine/gap_detector.py — detect_gaps
# ===========================================================================


class TestDetectGapsHappyPath:
    """Normal gap-detection scenarios."""

    def test_no_gaps_when_all_branches_covered(self):
        """No gaps emitted when mapped tests mention every branch scenario."""
        fn = FunctionInfo(
            name="discount",
            lineno=1,
            branches=[BranchInfo(expression="customer_type == 'vip'", kind="if")],
        )
        # mapped test name contains the literal from the expression ("vip")
        tm = _make_test_map(discount=[_mapped("test_vip_discount")])
        gaps = detect_gaps([fn], tm)
        assert gaps == []

    def test_gap_emitted_for_untested_branch(self):
        """A gap is produced when a branch has no matching test."""
        fn = FunctionInfo(
            name="route",
            lineno=1,
            branches=[BranchInfo(expression="method == 'DELETE'", kind="if")],
        )
        tm = _make_test_map()  # no mapped tests at all
        gaps = detect_gaps([fn], tm)
        assert len(gaps) == 1
        assert gaps[0].function == "route"

    def test_gap_id_increments(self):
        """Each gap gets a unique GAP-NNN identifier."""
        fn = FunctionInfo(
            name="multi",
            lineno=1,
            branches=[
                BranchInfo(expression="x == 'alpha'", kind="if"),
                BranchInfo(expression="x == 'beta'", kind="elif"),
            ],
        )
        tm = _make_test_map()
        gaps = detect_gaps([fn], tm)
        assert len(gaps) == 2
        assert gaps[0].id == "GAP-001"
        assert gaps[1].id == "GAP-002"

    def test_low_severity_for_function_without_branches_or_tests(self):
        """A function with no branches and no tests gets a low-severity gap."""
        fn = FunctionInfo(name="helper", lineno=1)
        tm = _make_test_map()
        gaps = detect_gaps([fn], tm)
        assert len(gaps) == 1
        assert gaps[0].severity == "low"
        assert gaps[0].scenario == "no branch coverage"

    def test_no_gap_when_function_has_no_branches_but_has_tests(self):
        """A branch-free function with a mapped test generates no gap."""
        fn = FunctionInfo(name="helper", lineno=1)
        tm = _make_test_map(helper=[_mapped("test_helper_basic")])
        gaps = detect_gaps([fn], tm)
        assert gaps == []

    def test_high_severity_for_auth_branch(self):
        """Branches containing security keywords are flagged high severity."""
        fn = FunctionInfo(
            name="login",
            lineno=1,
            branches=[BranchInfo(expression="is_admin == True", kind="if")],
        )
        tm = _make_test_map()
        gaps = detect_gaps([fn], tm)
        assert len(gaps) == 1
        assert gaps[0].severity == "high"

    def test_medium_severity_for_plain_if(self):
        """A plain if-branch with no security keyword gets medium severity."""
        fn = FunctionInfo(
            name="process",
            lineno=1,
            branches=[BranchInfo(expression="count > 0", kind="if")],
        )
        tm = _make_test_map()
        gaps = detect_gaps([fn], tm)
        assert len(gaps) == 1
        assert gaps[0].severity == "medium"

    def test_low_severity_for_else_branch(self):
        """An else branch gets low severity when not covered."""
        fn = FunctionInfo(
            name="check",
            lineno=1,
            branches=[BranchInfo(expression="default", kind="else")],
        )
        tm = _make_test_map()
        gaps = detect_gaps([fn], tm)
        # if a gap is raised, it must be low
        for gap in gaps:
            assert gap.severity == "low"

    def test_else_branch_skipped_when_covered_by_default_test(self):
        """An else/fallback branch is not flagged if a 'default' test exists."""
        fn = FunctionInfo(
            name="handle",
            lineno=1,
            branches=[BranchInfo(expression="default", kind="else")],
        )
        tm = _make_test_map(handle=[_mapped("test_handle_default_case")])
        gaps = detect_gaps([fn], tm)
        assert gaps == []

    def test_suggested_test_name_format(self):
        """suggested_test is always a valid Python identifier prefixed 'test_'."""
        fn = FunctionInfo(
            name="pay",
            lineno=1,
            branches=[BranchInfo(expression="currency == 'USD'", kind="if")],
        )
        tm = _make_test_map()
        gaps = detect_gaps([fn], tm)
        assert len(gaps) == 1
        assert gaps[0].suggested_test.startswith("test_")

    def test_empty_functions_list(self):
        """No functions → no gaps."""
        gaps = detect_gaps([], _make_test_map())
        assert gaps == []

    def test_multiple_functions_each_contribute_gaps(self):
        """Gaps from multiple functions are all collected in one list."""
        fns = [
            FunctionInfo(name="fn_a", lineno=1,
                         branches=[BranchInfo(expression="a == 1", kind="if")]),
            FunctionInfo(name="fn_b", lineno=5,
                         branches=[BranchInfo(expression="b == 2", kind="if")]),
        ]
        tm = _make_test_map()
        gaps = detect_gaps(fns, tm)
        functions_with_gaps = {g.function for g in gaps}
        assert "fn_a" in functions_with_gaps
        assert "fn_b" in functions_with_gaps


class TestDetectGapsIntegration:
    """Combine analyze_source output directly into detect_gaps."""

    def test_end_to_end_gap_detection(self):
        """analyze_source → detect_gaps pipeline produces correct gap count."""
        src = textwrap.dedent("""\
            def compute(value):
                if value > 0:
                    return "positive"
                elif value == 0:
                    return "zero"
                else:
                    return "negative"
        """)
        analysis = analyze_source(src)
        assert analysis.parse_error is None
        tm = _make_test_map()
        gaps = detect_gaps(analysis.functions, tm)
        # if + elif + else = 3 potential gaps
        assert len(gaps) >= 2

    def test_end_to_end_no_gaps_when_covered(self):
        """A function fully covered by tests produces zero gaps."""
        src = textwrap.dedent("""\
            def classify(role):
                if role == 'admin':
                    return True
                return False
        """)
        analysis = analyze_source(src)
        # provide a test that mentions "admin"
        tm = _make_test_map(classify=[_mapped("test_classify_admin_role")])
        gaps = detect_gaps(analysis.functions, tm)
        # the "if" branch scenario is "admin scenario" → "admin" key is in the
        # test name, so no gap should be raised for the if-branch.
        if_gaps = [g for g in gaps if g.scenario == "admin scenario"]
        assert if_gaps == []
