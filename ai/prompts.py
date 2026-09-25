"""Reusable IBM Bob 2.0 task prompts.

These are the exact prompts documented for the hackathon submission.
Each prompt is designed to be pasted into IBM Bob (or a compatible
AI development partner) as part of the ProofChange workflow.

The prompts are also used by `ai/bob_adapter.py` when running in
`runtime_llm` mode against any OpenAI-compatible endpoint.
"""

REPOSITORY_UNDERSTANDING = """\
You are a senior software engineer performing repository understanding.

Given:
- a unified diff of a change
- the affected source files
- the existing test files

Identify:
1. The functions/classes affected by the change.
2. The execution paths or branches introduced or modified.
3. The existing tests that map to those functions.
4. Potentially untested execution scenarios.

Return JSON matching this schema:
{
  "affected_functions": ["..."],
  "inferred_paths": ["..."],
  "mapped_tests": ["..."],
  "potentially_untested": ["..."]
}

Do not claim formal coverage. Use the language "inferred" and
"potentially affected".
"""

TEST_GAP_ANALYSIS = """\
You are a senior test engineer.

Given the changed code, affected functions, existing tests, and
inferred execution paths, identify meaningful test scenarios that
are missing.

For each gap return:
{
  "id": "GAP-NNN",
  "function": "...",
  "scenario": "...",
  "reason": "...",
  "severity": "low|medium|high",
  "suggested_test": "test_..."
}

Rules:
- Do not flag scenarios already covered by mapped tests.
- Prefer high-signal scenarios over exhaustive branch enumeration.
- Do not claim mathematical completeness.
"""

TEST_GENERATION = """\
You are a senior software test engineer.

Generate focused pytest tests for the identified gaps.

Rules:
- Follow the existing test style in the repository.
- Do not modify production code.
- Do not weaken assertions merely to make tests pass.
- One test per gap where possible.
- Use plain `assert` statements.

Return a JSON array of:
{
  "test_name": "test_...",
  "file": "tests/...",
  "code": "def test_...():\\n    ...",
  "targets_gap": "GAP-NNN"
}
"""

FAILURE_ANALYSIS = """\
You are a senior engineer performing failure analysis.

Given a failing generated test, determine whether the failure is
caused by:
- incorrect test assumptions
- incorrect production behavior
- environment/configuration
- unrelated failure

Do not simply modify assertions to make tests pass.
Return a short structured analysis with a recommended action.
"""

VERIFICATION_SUMMARY = """\
Produce a concise verification summary describing:
- changed files
- affected functions
- existing relevant tests
- detected gaps
- generated tests
- executed tests
- passed tests
- failed tests
- unresolved paths
- evidence strength

Do not claim formal proof. Use the term "verification evidence".
"""

ALL_PROMPTS = {
    "repository_understanding": REPOSITORY_UNDERSTANDING,
    "test_gap_analysis": TEST_GAP_ANALYSIS,
    "test_generation": TEST_GENERATION,
    "failure_analysis": FAILURE_ANALYSIS,
    "verification_summary": VERIFICATION_SUMMARY,
}