# ProofChange — Architecture Diagram

```mermaid
flowchart TD

    %% ── Entry Points ──────────────────────────────────────────────────────────
    subgraph Entry["Entry Points"]
        APP["app.py\nStreamlit UI\n(Evidence Center)"]
        GH_HOOK["GitHub Webhook\ngithub/webhook.py\nHMAC-verified POST /webhook"]
    end

    %% ── API / Routing ─────────────────────────────────────────────────────────
    subgraph APILayer["API Layer"]
        PIPELINE_DEMO["pipeline.run_demo_pipeline()"]
        PIPELINE_CUSTOM["pipeline.analyze_custom_diff()"]
    end

    APP -->|"Run Demo Pipeline"| PIPELINE_DEMO
    GH_HOOK -->|"pull_request opened/sync/reopened\nextract_pr_event()"| PIPELINE_CUSTOM

    %% ── Core Pipeline ─────────────────────────────────────────────────────────
    subgraph Pipeline["Core Pipeline  (pipeline.py)"]
        direction TB

        DIFF["① Diff Analysis\nengine/diff_analyzer.py\nanalyze_diff()\n→ DiffAnalysis"]
        CODE["② Code Analysis\nengine/code_analyzer.py\nanalyze_source() / analyze_file()\n→ CodeAnalysis"]
        TESTMAP["③ Test Mapping\nengine/test_mapper.py\nmap_tests()\n→ TestMap"]
        GAP["④ Gap Detection\nengine/gap_detector.py\ndetect_gaps()\n→ list[GapInfo]"]
        TESTGEN["⑤ Test Generation\nai/test_generator.py\ngenerate_tests()\n→ list[GeneratedTest]"]
        EXEC["⑥ Execution\nengine/runner.py\nrun_pytest()\n→ ExecutionResult"]
        IMPACT["⑦ Impact Summary\nengine/impact_analyzer.py\nsummarize_impact()\n→ ImpactSummary"]
        EVIDENCE["⑧ Evidence Package\nengine/evidence.py\nbuild_package() + save_package()\n→ EvidencePackage (JSON)"]

        DIFF --> CODE --> TESTMAP --> GAP --> TESTGEN --> EXEC --> IMPACT --> EVIDENCE
    end

    PIPELINE_DEMO --> DIFF
    PIPELINE_CUSTOM --> DIFF

    %% ── Bob Adapter (two modes) ───────────────────────────────────────────────
    subgraph BobAdapter["IBM Bob Adapter  (ai/bob_adapter.py)"]
        direction TB
        BOB_CHECK{"AI_MODE\nenv var"}

        subgraph DocMode["Mode A · documented_bob_workflow  (default)"]
            DOC_STUB["_documented_stub()\nReturns structured prompt\nfrom ai/prompts.py\n(no network call)"]
        end

        subgraph RuntimeMode["Mode B · runtime_llm"]
            RUNTIME_CALL["_call_bob()\nPOST BOB_API_URL/chat/completions\nOpenAI-compatible · model bob-2.0"]
            FALLBACK["Fallback on error →\nruntime_llm_failed\n(returns error note)"]
            RUNTIME_CALL -->|"HTTP error / timeout"| FALLBACK
        end

        BOB_CHECK -->|"BOB_API_URL + BOB_API_KEY absent\nor AI_MODE ≠ runtime_llm"| DOC_STUB
        BOB_CHECK -->|"BOB_API_URL + BOB_API_KEY set\nand AI_MODE = runtime_llm"| RUNTIME_CALL
    end

    TESTGEN -->|"BobAdapter.generate_tests()"| BOB_CHECK
    GAP     -->|"BobAdapter.detect_gaps()"| BOB_CHECK

    %% ── GitHub Integration ────────────────────────────────────────────────────
    subgraph GitHubIntegration["GitHub Integration  (github/)"]
        direction TB
        WEBHOOK_PARSE["webhook.py\nparse_github_webhook()\nverify_signature (HMAC-SHA256)"]
        GH_EXTRACT["webhook.py\nextract_pr_event()\nNormalises PR metadata"]
        GH_CLIENT["client.py\nGitHub REST client"]
        GH_CHECKS["checks.py\nformat_check()\n→ GitHub Check Run payload"]
        GH_REPO["repo.py\nRepo file / diff fetch"]
        GH_AUTH["auth.py\nGitHub App auth / token"]
    end

    GH_HOOK --> WEBHOOK_PARSE --> GH_EXTRACT --> PIPELINE_CUSTOM
    EVIDENCE -->|"EvidencePackage"| GH_CHECKS
    GH_CHECKS -->|"POST checks API"| GH_CLIENT
    GH_CLIENT --> GH_AUTH
    PIPELINE_CUSTOM -->|"fetch diff / source"| GH_REPO
    GH_REPO --> GH_CLIENT

    %% ── UI Pages (app.py) ─────────────────────────────────────────────────────
    subgraph UI["Streamlit Pages  (app.py)"]
        direction LR
        P1["Overview"] --- P2["Change Analysis"]
        P2 --- P3["Test Gaps"]
        P3 --- P4["Generated Tests"]
        P4 --- P5["Verification"]
        P5 --- P6["Evidence"]
        P6 --- P7["GitHub"]
        P7 --- P8["IBM Bob"]
    end

    EVIDENCE -->|"EvidencePackage\n→ session_state.pkg"| UI

    %% ── Styling ───────────────────────────────────────────────────────────────
    style Entry           fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    style APILayer        fill:#f0fdf4,stroke:#16a34a,color:#14532d
    style Pipeline        fill:#fefce8,stroke:#ca8a04,color:#713f12
    style BobAdapter      fill:#faf5ff,stroke:#7c3aed,color:#3b0764
    style DocMode         fill:#ede9fe,stroke:#7c3aed,color:#3b0764
    style RuntimeMode     fill:#ddd6fe,stroke:#7c3aed,color:#3b0764
    style GitHubIntegration fill:#fff1f2,stroke:#e11d48,color:#881337
    style UI              fill:#f0f9ff,stroke:#0284c7,color:#0c4a6e
```

## Key Components

| Layer | Files | Responsibility |
|---|---|---|
| **Entry — UI** | `app.py` | Streamlit dashboard; 8 navigation pages; triggers `run_demo_pipeline()` |
| **Entry — GitHub** | `github/webhook.py` | HMAC-SHA256-verified webhook; normalises PR events |
| **Pipeline** | `pipeline.py` | Orchestrates all 8 stages; shared by UI and webhook paths |
| **Diff Analysis** | `engine/diff_analyzer.py` | Parses unified diffs → `DiffAnalysis` |
| **Code Analysis** | `engine/code_analyzer.py` | AST-based function/branch extraction → `CodeAnalysis` |
| **Test Mapping** | `engine/test_mapper.py` | Maps source functions to existing test files → `TestMap` |
| **Gap Detection** | `engine/gap_detector.py` | Identifies untested branches → `list[GapInfo]` |
| **Test Generation** | `ai/test_generator.py` | Produces `GeneratedTest` objects via Bob adapter |
| **Execution** | `engine/runner.py` | Runs pytest; captures pass/fail → `ExecutionResult` |
| **Impact Analysis** | `engine/impact_analyzer.py` | Summarises change risk → `ImpactSummary` |
| **Evidence** | `engine/evidence.py` | Builds + persists `EvidencePackage` (JSON + Markdown) |
| **Bob Adapter** | `ai/bob_adapter.py` | **Mode A** `documented_bob_workflow`: returns prompt stubs (no API call). **Mode B** `runtime_llm`: calls `BOB_API_URL/chat/completions` with fallback |
| **GitHub Checks** | `github/checks.py` | Converts `EvidencePackage` → GitHub Check Run payload |
| **GitHub Client** | `github/client.py` + `auth.py` | REST calls + App token auth |
