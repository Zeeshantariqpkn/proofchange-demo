# ProofChange — Executive Summary

> **AI Change Verification for Software Teams**
> *Hackathon submission — IBM Bob 2.0 track*

---

## The Problem: CI Green ≠ Change Verified

Continuous integration answers one question: *"Did the configured tests pass?"*

It does not answer the question that actually matters after a code change:
*"Is the newly changed behavior adequately verified?"*

A pull request can introduce a new branch, a new execution path, or a new edge
case while CI stays entirely green — because the existing test suite never
exercises the new code. The tests were written for the old behavior. No test
ever fails. The change ships unverified.

This is not a test-quality problem. It is a **test-coverage blindspot at the
point of change**, and every team that relies on CI as its only safety signal
has it.

---

## The Solution: Change Evidence, Not Just Test Generation

ProofChange is a verification layer that closes the gap between "CI passed" and
"this change is verified." Its core output is a **Change Evidence Package** — a
structured artifact that answers:

- Which functions did this change touch?
- Which execution paths were added or modified?
- Which of those paths have existing test coverage?
- Which scenarios are untested (test gaps)?
- Were tests generated and executed for those gaps?
- What is the overall evidence strength for this change?

The pipeline runs automatically on every diff:

| Step | Engine component | What it does |
|---|---|---|
| 1. Diff parsing | `engine/diff_analyzer` | Extracts changed files, line ranges, added conditionals |
| 2. Code analysis | `engine/code_analyzer` | Python AST walk — maps functions, branches, execution paths |
| 3. Test mapping | `engine/test_mapper` | Links existing tests to affected functions by name heuristics |
| 4. Gap detection | `engine/gap_detector` | Finds branches with no mapped test scenario |
| 5. Test generation | `ai/test_generator` | Produces focused pytest tests targeting each gap |
| 6. Execution | `engine/runner` | Runs real `pytest` against the generated tests |
| 7. Evidence | `engine/evidence` | Aggregates all steps into a scored Evidence Package |

The Evidence Package carries a transparent **evidence level** — `STRONG`,
`PARTIAL`, or `INSUFFICIENT` — computed by explicit, auditable rules (not an
LLM opinion): all gaps addressed + ≥70% paths verified → `STRONG`.

---

## How IBM Bob Was Used

IBM Bob 2.0 was the development partner throughout the project and is a
first-class part of the runtime architecture.

**During development — Bob as IDE assistant:**

| Task | How Bob was used |
|---|---|
| Architecture walkthrough | Bob traced the full pipeline module graph |
| Gap detector deep dive | Bob walked the execution trace through `gap_detector` logic |
| `ai_assisted_steps` field | Added to `EvidencePackage` with Bob's guidance |
| Edge-case tests | Bob wrote `test_zero_price` and `test_vip_beats_premium` |
| README + docs | Generated and refined with Bob |

**At runtime — Bob as the AI adapter (`ai/bob_adapter.py`):**

ProofChange exposes five documented Bob task prompts in `ai/prompts.py`, each
mapping 1-to-1 to a pipeline step:

1. **Repository Understanding** — identify affected functions and untested scenarios
2. **Test Gap Analysis** — review changed code against existing tests
3. **Test Generation** — produce focused pytest tests for missing scenarios
4. **Failure Analysis** — classify failing generated tests (don't weaken assertions)
5. **Verification Summary** — produce the human-readable evidence summary

The adapter runs in `documented_bob_workflow` mode by default (prompts are used
with IBM Bob IDE) or in `runtime_llm` mode when a Bob-compatible OpenAI-shaped
endpoint is configured. Every generated artifact records its source
(`"bob-assisted"` or `"runtime_llm"`) so the origin of every decision is always
traceable. No undocumented IBM API is assumed.

---

## The Workflow: CHANGE → PROVE

```
PR / diff
    │
    ▼
diff_analyzer ──► code_analyzer ──► test_mapper
                                         │
                                         ▼
                                    gap_detector
                                         │
                                         ▼
                                   test_generator  ◄── IBM Bob
                                         │
                                         ▼
                                      runner  (real pytest)
                                         │
                                         ▼
                                   evidence engine
                                    /           \
                           Evidence            GitHub
                           Center UI          Check Run
                        (Streamlit)
```

The demo change — adding a `vip` discount tier to `calculate_discount()` — runs
the full pipeline end-to-end: the diff is parsed, the new `if customer_type ==
"vip"` branch is detected, the gap is identified (no test for the `vip`
scenario), a pytest test is generated, executed, and the resulting Evidence
Package is published as a GitHub Check Run and displayed in the Evidence Center
dashboard.

---

## What Makes ProofChange Different from AI Test Generators

| Dimension | AI test generators | ProofChange |
|---|---|---|
| **Scope** | Whole repo or arbitrary prompt | Scoped to the specific change in the PR |
| **Input** | "Generate tests for this file/function" | The diff itself — change is the anchor |
| **Output** | Test code suggestions | A scored **Change Evidence Package** |
| **Gap detection** | Not performed — tests are generated speculatively | AST-driven — gaps are detected before generation |
| **Execution** | Usually not included | Real `pytest` execution is a mandatory pipeline step |
| **Verdict** | None — user decides if tests are good | `STRONG / PARTIAL / INSUFFICIENT` with an auditable rationale |
| **Traceability** | Tests disconnected from change reasoning | Every artifact traces back to a specific gap and branch |
| **AI role** | AI *is* the product | AI *assists* the pipeline — the engine runs deterministically without it |

The key insight: **test generation is step 5 of 7**. ProofChange first proves
that a gap exists (steps 1–4) and then proves the gap is closed (steps 6–7).
The generated test is evidence, not the product.
