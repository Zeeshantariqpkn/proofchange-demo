"""ProofChange Evidence Center - Streamlit UI.

A light, enterprise-style dashboard that walks through the full
ProofChange workflow and displays the Change Evidence Package.
"""
from __future__ import annotations

import json
import os

import streamlit as st
from dotenv import load_dotenv

from dashboard import components as ui
from engine import evidence as evidence_engine
from pipeline import run_demo_pipeline

load_dotenv()

st.set_page_config(
    page_title="ProofChange - Evidence Center",
    page_icon=":mag:",
    layout="wide",
    initial_sidebar_state="expanded",
)

ui.inject_styles()


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

st.sidebar.markdown(
    """
    <div style="padding: 0.5rem 0 0.75rem 0;">
        <div style="font-size:1.25rem;font-weight:800;color:#0f172a;">ProofChange</div>
        <div style="color:#475569;font-size:0.8rem;">AI Change Verification</div>
    </div>
    """,
    unsafe_allow_html=True,
)

PAGES = [
    "Overview",
    "Change Analysis",
    "Test Gaps",
    "Generated Tests",
    "Verification",
    "Evidence",
    "GitHub",
    "IBM Bob",
]
page = st.sidebar.radio("Navigate", PAGES, label_visibility="collapsed")

st.sidebar.markdown("---")
demo_mode = st.sidebar.toggle("Demo Mode", value=True)
run_button = st.sidebar.button("Run Demo Pipeline", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Demo Mode analyzes the bundled demo_repo and executes pytest "
    "locally. No GitHub credentials required."
)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "pkg" not in st.session_state:
    st.session_state.pkg = None
if "run_error" not in st.session_state:
    st.session_state.run_error = None


def _run() -> None:
    try:
        with st.spinner("Running ProofChange pipeline..."):
            pkg = run_demo_pipeline(
                repository="demo_repo",
                commit="8f3a92d",
                pr_number=17,
                pr_title="Add VIP discount support",
            )
        st.session_state.pkg = pkg
        st.session_state.run_error = None
    except Exception as exc:
        st.session_state.run_error = str(exc)
        st.session_state.pkg = None


if run_button:
    _run()

if demo_mode and st.session_state.pkg is None and st.session_state.run_error is None:
    _run()


pkg = st.session_state.pkg


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_pkg() -> bool:
    if st.session_state.run_error:
        st.error(f"Pipeline error: {st.session_state.run_error}")
        return False
    if pkg is None:
        st.info("Click Run Demo Pipeline in the sidebar to generate evidence.")
        return False
    return True


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

if page == "Overview":
    ui.hero()
    st.markdown("### From change to evidence, in one workflow.")
    st.write(
        "ProofChange analyzes a code change, identifies affected functions and "
        "execution paths, maps existing tests, detects missing scenarios, assists "
        "with test generation, executes tests, and produces a Change Evidence Package."
    )
    ui.workflow_flow()

    if not _require_pkg():
        st.stop()

    d = pkg.to_dict()
    ui.kpi_row([
        ("Files Changed", d["change"]["files_changed"], None),
        ("Functions Affected", d["change"]["functions_affected"], None),
        ("Test Gaps", d["testing"]["test_gaps"], None),
        ("Generated Tests", d["testing"]["generated_tests"], None),
        ("Tests Passed", str(d["execution"]["passed"]) + "/" + str(d["execution"]["tests_executed"]), None),
        ("Evidence", d["evidence"]["level"], d["evidence"]["level"]),
    ])

    st.markdown("")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("#### Pipeline result")
        st.markdown(
            "- **Change:** " + (pkg.pr_title or "Code change") + "\n"
            "- **Repository:** `" + pkg.repository + "`\n"
            "- **Commit:** `" + (pkg.commit or "n/a") + "`\n"
            "- **AI mode:** `" + pkg.ai_mode + "`\n"
            "- **Evidence:** **" + d["evidence"]["level"] + "**"
        )
    with col2:
        st.markdown("#### Rationale")
        st.info(d["evidence"]["rationale"])


elif page == "Change Analysis":
    ui.hero()
    st.markdown("### Change Analysis")
    if not _require_pkg():
        st.stop()

    d = pkg.to_dict()
    st.markdown("**PR #" + str(pkg.pr_number or 0) + " - " + (pkg.pr_title or "Code change") + "**")
    st.markdown("Files changed: **" + str(d["change"]["files_changed"]) + "**")

    ui.section("Changed files")
    for f in d["artifacts"]["diff"]["files"]:
        header = f["path"] + "  |  +" + str(f["added_lines"]) + "  -" + str(f["deleted_lines"])
        with st.expander(header, expanded=True):
            if f.get("functions"):
                st.markdown("**Functions affected:** " + ", ".join(f["functions"]))
            if f.get("added_conditionals"):
                st.markdown("**Added conditionals:**")
                for c in f["added_conditionals"]:
                    st.code(c, language="python")
            if f.get("raw_diff"):
                st.code(f["raw_diff"], language="diff")

    ui.section("Inferred execution paths")
    for ca in d["artifacts"]["code"]:
        for fn in ca["functions"]:
            st.markdown("**" + fn["name"] + "()**")
            for b in fn["branches"]:
                st.markdown("- `" + b["expression"] + "`  _(" + b["kind"] + ")_")


elif page == "Test Gaps":
    ui.hero()
    st.markdown("### Test Gaps")
    if not _require_pkg():
        st.stop()
    gaps = pkg.to_dict()["artifacts"]["gaps"]
    if not gaps:
        st.success("No test gaps detected for the analyzed change.")
    else:
        for g in gaps:
            st.markdown(
                '<div class="pc-card" style="margin-bottom:0.75rem">'
                '<div style="display:flex;justify-content:space-between;align-items:center">'
                '<strong>GAP ' + g['id'] + ' - ' + g['scenario'] + '</strong>'
                '<span class="pc-badge pc-badge-partial">' + g['severity'].upper() + '</span>'
                '</div>'
                '<div style="color:#475569;margin-top:0.4rem">'
                '<div><strong>Affected:</strong> <code>' + g['function'] + '()</code></div>'
                '<div><strong>Reason:</strong> ' + g['reason'] + '</div>'
                '<div><strong>Suggested test:</strong> <code>' + g['suggested_test'] + '</code></div>'
                '</div>'
                '</div>',
                unsafe_allow_html=True,
            )


elif page == "Generated Tests":
    ui.hero()
    st.markdown("### Generated Tests")
    if not _require_pkg():
        st.stop()
    gen = pkg.to_dict()["artifacts"]["generated_tests"]
    if not gen:
        st.info("No tests were generated (no gaps detected).")
    else:
        for gt in gen:
            st.markdown("#### `" + gt["test_name"] + "`")
            st.caption(
                "Generated by: **" + gt["source"] + "**  |  "
                "Targets gap: `" + gt["targets_gap"] + "`  |  File: `" + gt["file"] + "`"
            )
            st.code(gt["code"], language="python")
            st.markdown(
                "<div style='color:#475569'>Status: <strong>Ready for verification</strong></div>",
                unsafe_allow_html=True,
            )


elif page == "Verification":
    ui.hero()
    st.markdown("### Test Execution")
    if not _require_pkg():
        st.stop()
    d = pkg.to_dict()
    ex = d["execution"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Executed", ex["tests_executed"])
    c2.metric("Passed", ex["passed"])
    c3.metric("Failed", ex["failed"])
    c4.metric("Duration", str(ex["duration_s"]) + "s")

    ui.section("Raw pytest output")
    with st.expander("stdout", expanded=True):
        st.code(d["artifacts"].get("execution_stdout", "") or "(empty)", language="text")
    with st.expander("stderr", expanded=False):
        st.code(d["artifacts"].get("execution_stderr", "") or "(empty)", language="text")


elif page == "Evidence":
    ui.hero()
    st.markdown("# Change Evidence")
    if not _require_pkg():
        st.stop()
    d = pkg.to_dict()

    st.markdown(
        '<div class="pc-card" style="margin-bottom:1rem">'
        '<div class="pc-kpi-label">Commit</div>'
        '<div class="pc-kpi-value" style="font-size:1.1rem">' + (pkg.commit or "n/a") + '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        ui.section("Change")
        st.markdown(
            "- Files changed: **" + str(d['change']['files_changed']) + "**\n"
            "- Functions affected: **" + str(d['change']['functions_affected']) + "**\n"
            "- Existing tests: **" + str(d['testing']['existing_tests']) + "**\n"
            "- Missing scenarios: **" + str(d['testing']['test_gaps']) + "**\n"
            "- Generated tests: **" + str(d['testing']['generated_tests']) + "**"
        )
    with col2:
        ui.section("Execution")
        st.markdown(
            "- Tests: **" + str(d['execution']['tests_executed']) + "**\n"
            "- Passed: **" + str(d['execution']['passed']) + "**\n"
            "- Failed: **" + str(d['execution']['failed']) + "**"
        )
        ui.section("Path Evidence")
        st.markdown(
            "- Verified: **" + str(d['paths']['verified']) + "**\n"
            "- Partial: **" + str(d['paths']['partial']) + "**\n"
            "- Unresolved: **" + str(d['paths']['unresolved']) + "**"
        )

    ui.section("Evidence")
    level = d["evidence"]["level"]
    st.markdown(
        '<span class="pc-badge pc-badge-' + level.lower() + '">' + level + '</span>',
        unsafe_allow_html=True,
    )
    st.caption(d["evidence"]["rationale"])

    ui.section("Included artifacts")
    st.markdown(
        "- Changed-code map\n"
        "- Impact analysis\n"
        "- Test-gap report\n"
        "- Generated tests\n"
        "- Execution report\n"
        "- Verification summary"
    )

    st.download_button(
        "Download Evidence JSON",
        data=json.dumps(d, indent=2),
        file_name="proofchange_evidence_" + pkg.id + ".json",
        mime="application/json",
    )
    st.download_button(
        "Download Evidence Markdown",
        data=evidence_engine.to_markdown(pkg),
        file_name="proofchange_evidence_" + pkg.id + ".md",
        mime="text/markdown",
    )


elif page == "GitHub":
    ui.hero()
    st.markdown("### GitHub Integration")
    st.write(
        "ProofChange is designed as a GitHub App. It listens for "
        "pull_request events (opened, synchronize, reopened), "
        "analyzes the diff, and publishes a Check Run titled "
        "ProofChange - Change Verification."
    )

    st.markdown("#### Example Check Run output")
    if pkg is not None:
        from github.checks import format_check
        check = format_check(pkg)
        st.code(check["summary"], language="text")
    else:
        st.info("Run the demo pipeline to generate an example check.")

    st.markdown("#### Configuration")
    st.markdown(
        "Set the following environment variables to enable live GitHub integration:\n\n"
        "```\n"
        "GITHUB_APP_ID=\n"
        "GITHUB_PRIVATE_KEY_PATH=\n"
        "GITHUB_WEBHOOK_SECRET=\n"
        "GITHUB_INSTALLATION_ID=\n"
        "```\n\n"
        "The webhook endpoint is POST /webhooks/github on the FastAPI service. "
        "Signature validation uses X-Hub-Signature-256."
    )
    st.warning(
        "For the hackathon, remote PR execution is not enabled by default. "
        "Arbitrary untrusted PR execution requires a production-grade "
        "sandbox (isolated containers, ephemeral runners, restricted "
        "network, minimal credentials, resource/time limits)."
    )


elif page == "IBM Bob":
    ui.hero()
    st.markdown("### IBM Bob 2.0 Usage")
    st.write(
        "IBM Bob 2.0 is used as the documented AI development partner for "
        "ProofChange. The adapter (ai/bob_adapter.py) supports two modes:"
    )
    st.markdown(
        "- **documented_bob_workflow** (default) - ProofChange runs the "
        "automated engine. The Bob task prompts in ai/prompts.py are "
        "documented and used with IBM Bob for repository understanding, "
        "gap analysis, test generation, failure analysis, and verification "
        "summaries.\n"
        "- **runtime_llm** (opt-in) - if AI_PROVIDER_BASE_URL, "
        "AI_PROVIDER_API_KEY, and AI_MODEL are configured, ProofChange "
        "calls an OpenAI-compatible endpoint for test generation and "
        "failure analysis. No undocumented IBM API is assumed."
    )

    from ai import prompts as bob_prompts
    st.markdown("#### Reusable Bob task prompts")
    for name, prompt in bob_prompts.ALL_PROMPTS.items():
        with st.expander(name.replace("_", " ").title(), expanded=False):
            st.code(prompt, language="text")

    st.markdown("#### Where Bob assisted")
    st.markdown(
        "- **Repository understanding** - identifying affected functions and "
        "potentially untested scenarios.\n"
        "- **Test-gap analysis** - reviewing changed code against existing tests.\n"
        "- **Test generation** - producing focused pytest tests for missing scenarios.\n"
        "- **Failure analysis** - classifying failing generated tests.\n"
        "- **Verification summary** - producing the human-readable evidence summary."
    )
    st.info(
        "See docs/bob-workflow.md for the full documented workflow, "
        "including which steps are automated by ProofChange and which are "
        "Bob-assisted."
    )