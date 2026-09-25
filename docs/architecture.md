# ProofChange Architecture

## Overview

ProofChange is an AI change verification layer. It turns a code change
into a Change Evidence Package by combining static analysis, test
mapping, gap detection, test generation, real execution, and evidence
scoring.

## Pipeline
GitHub PR / Demo Diff
│
▼
┌─────────────────────┐
│ diff_analyzer.py │ unified diff → changed files, added lines,
└─────────────────────┘ added conditionals
│
▼
┌─────────────────────┐
│ code_analyzer.py │ Python AST → functions, classes, branches,
└─────────────────────┘ return paths
│
▼
┌─────────────────────┐
│ test_mapper.py │ AST-based mapping of tests → functions
└─────────────────────┘
│
▼
┌─────────────────────┐
│ gap_detector.py │ inferred scenarios vs mapped tests
└─────────────────────┘
│
▼
┌─────────────────────┐
│ test_generator.py │ Bob-assisted / runtime LLM test generation
└─────────────────────┘
│
▼
┌─────────────────────┐
│ runner.py │ real pytest execution in a controlled dir
└─────────────────────┘
│
▼
┌─────────────────────┐
│ evidence.py │ Change Evidence Package + level scoring
└─────────────────────┘
│
├──► Streamlit Evidence Center
└──► GitHub Check Run


## Layers

- **engine/** — pure Python analysis. No I/O beyond reading source files.
- **ai/** — Bob adapter and prompts. Pluggable, provider-agnostic.
- **github/** — App-compatible webhook, client, and check formatting.
- **dashboard/** — Streamlit components.
- **api.py** — FastAPI surface for CI and webhooks.
- **pipeline.py** — the single orchestration entry point.
- **app.py** — the Streamlit Evidence Center.

## Evidence model

Evidence levels are computed from transparent rules:

- **INSUFFICIENT** — no execution evidence, or any failing test.
- **PARTIAL** — execution succeeded but high-severity gaps remain, or
  fewer than 70% of analyzed paths are verified.
- **STRONG** — execution succeeded, no high-severity gaps, and at
  least 70% of analyzed paths are verified.

Evidence strength reflects the amount of *executable and mapped*
evidence available for the analyzed change. It is **not** a formal
correctness proof.