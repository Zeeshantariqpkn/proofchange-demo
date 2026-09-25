# IBM Bob 2.0 Workflow

ProofChange uses IBM Bob 2.0 as the documented AI development partner
for the hackathon submission.

## Modes

The adapter `ai/bob_adapter.py` supports:

| Mode | When | What happens |
| --- | --- | --- |
| `documented_bob_workflow` | Default | ProofChange runs the automated engine. Bob task prompts are documented and used with IBM Bob. |
| `runtime_llm` | Opt-in | If `AI_PROVIDER_BASE_URL`, `AI_PROVIDER_API_KEY`, `AI_MODEL` are set, ProofChange calls an OpenAI-compatible endpoint. |

No undocumented IBM API is assumed. The architecture is Bob-compatible:
generated artifacts from a Bob session can be dropped into the
pipeline.

## Tasks

### Task 1 — Repository Understanding

> Analyze the repository and identify the functions affected by the
> supplied change. Map those functions to relevant existing tests and
> identify potentially untested execution scenarios.

**Used by:** `BobAdapter.analyze_change`, `ai/prompts.REPOSITORY_UNDERSTANDING`

### Task 2 — Test Gap Analysis

> Review the changed code, affected functions, existing tests, and
> inferred execution paths. Identify meaningful test scenarios that are
> missing.

**Used by:** `BobAdapter.detect_gaps`, `ai/prompts.TEST_GAP_ANALYSIS`

### Task 3 — Test Generation

> Generate focused pytest tests for the identified gaps. Follow the
> existing test style. Do not modify production code. Do not weaken
> assertions.

**Used by:** `BobAdapter.generate_tests`, `ai/prompts.TEST_GENERATION`

### Task 4 — Failure Analysis

> Review failing generated tests and determine whether the failure is
> caused by incorrect test assumptions, incorrect production behavior,
> environment/configuration, or an unrelated failure. Do not simply
> modify assertions to make tests pass.

**Used by:** `BobAdapter.analyze_failure`, `ai/prompts.FAILURE_ANALYSIS`

### Task 5 — Verification Summary

> Produce a concise verification summary describing changed files,
> affected functions, existing relevant tests, detected gaps, generated
> tests, executed tests, passed tests, failed tests, unresolved paths,
> and evidence strength.

**Used by:** `BobAdapter.create_summary`, `ai/prompts.VERIFICATION_SUMMARY`

## What is automated vs Bob-assisted

| Step | Automated by ProofChange | Bob-assisted |
| --- | --- | --- |
| Diff parsing | ✅ | |
| AST code analysis | ✅ | |
| Test mapping | ✅ | |
| Gap detection | ✅ | |
| Repository understanding | | ✅ |
| Test generation | ✅ (template) / ✅ (runtime LLM) | ✅ |
| Test execution | ✅ | |
| Failure analysis | | ✅ |
| Verification summary | ✅ | ✅ |

## Evidence placeholders

Screenshots and session transcripts should be placed in
`docs/screenshots/`. Suggested files:

- `docs/screenshots/bob-task-1-repo-understanding.png`
- `docs/screenshots/bob-task-2-gap-analysis.png`
- `docs/screenshots/bob-task-3-test-generation.png`
- `docs/screenshots/bob-task-4-failure-analysis.png`
- `docs/screenshots/bob-task-5-verification-summary.png`
- `docs/screenshots/proofchange-evidence-center.png`
- `docs/screenshots/github-check-run.png`