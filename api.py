"""ProofChange FastAPI application.

Exposes the analysis pipeline over HTTP and provides GitHub webhook
handling. The Streamlit UI talks to the same pipeline directly, so
this API is optional for the demo but required for GitHub integration.
"""
from __future__ import annotations

import os
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from ai.bob_adapter import BobAdapter
from engine import diff_analyzer, evidence as evidence_engine
from engine.code_analyzer import analyze_source
from engine.gap_detector import detect_gaps
from engine.impact_analyzer import summarize_impact
from engine.models import (
    CodeAnalysis,
    DiffAnalysis,
    GeneratedTest,
    TestGap,
    TestMap,
)
from engine.runner import run_pytest
from engine.test_mapper import map_tests
from github import webhook as gh_webhook

load_dotenv()

app = FastAPI(title="ProofChange", version="0.1.0")
DATA_DIR = os.environ.get("PROOFCHANGE_DATA_DIR", "./data")
OUTPUT_DIR = os.environ.get("PROOFCHANGE_OUTPUT_DIR", "./output")

_adapter = BobAdapter()


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class AnalyzeDiffRequest(BaseModel):
    diff: str = Field(..., description="Unified diff text")
    repository: str = "demo_repo"
    commit: str = ""
    pr_number: Optional[int] = None
    pr_title: str = ""
    tests_root: str = "demo_repo/tests"
    source_root: str = "demo_repo/src"


class AnalyzeRequest(BaseModel):
    repository: str = "demo_repo"
    commit: str = ""
    pr_number: Optional[int] = None
    pr_title: str = ""


class GenerateTestsRequest(BaseModel):
    gaps: list[dict[str, Any]]
    functions: list[dict[str, Any]]
    tests_root: str = "demo_repo/tests"


class VerifyRequest(BaseModel):
    target_dir: str = "demo_repo"
    extra_args: list[str] = []


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "proofchange"}


@app.post("/analyze/diff")
def analyze_diff_endpoint(req: AnalyzeDiffRequest) -> dict[str, Any]:
    analysis = diff_analyzer.analyze_diff(req.diff)
    return analysis.to_dict()


@app.post("/analyze")
def analyze_endpoint(req: AnalyzeRequest) -> dict[str, Any]:
    """Run the demo pipeline against the bundled demo_repo."""
    from pipeline import run_demo_pipeline

    try:
        pkg = run_demo_pipeline(
            repository=req.repository,
            commit=req.commit or "demo",
            pr_number=req.pr_number,
            pr_title=req.pr_title or "Demo change",
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return pkg.to_dict()


@app.post("/generate-tests")
def generate_tests_endpoint(req: GenerateTestsRequest) -> dict[str, Any]:
    from engine.models import FunctionInfo, TestGap
    from ai.test_generator import generate_tests

    gaps = [TestGap(**g) for g in req.gaps]
    functions = []
    for f in req.functions:
        branches = f.get("branches", [])
        from engine.models import BranchInfo
        functions.append(
            FunctionInfo(
                name=f["name"],
                lineno=f.get("lineno", 0),
                args=f.get("args", []),
                branches=[BranchInfo(**b) for b in branches],
                return_paths=f.get("return_paths", 0),
                calls=f.get("calls", []),
            )
        )
    generated = generate_tests(gaps, functions, _adapter, req.tests_root)
    return {"generated": [g.to_dict() for g in generated]}


@app.post("/verify")
def verify_endpoint(req: VerifyRequest) -> dict[str, Any]:
    result = run_pytest(req.target_dir, extra_args=req.extra_args)
    return result.to_dict()

@app.post("/webhooks/github")
async def github_webhook(request: Request) -> dict[str, Any]:
    import shutil
    from github.auth import get_installation_token
    from github.checks import format_check
    from github.client import GitHubClient
    from github.repo import clone_pr_head
    from pipeline import analyze_custom_diff

    parsed = await gh_webhook.parse_github_webhook(request)
    event = gh_webhook.extract_pr_event(parsed["event"], parsed["payload"])
    if event is None:
        return {"status": "ignored", "reason": "unsupported event"}

    app_id = os.environ.get("GITHUB_APP_ID", "").strip()
    key_path = os.environ.get("GITHUB_PRIVATE_KEY_PATH", "").strip()
    install_id = os.environ.get("GITHUB_INSTALLATION_ID", "").strip()

    if not (app_id and key_path and install_id):
        return {
            "status": "accepted",
            "event": event,
            "note": "GitHub App credentials not configured; dry-run only.",
        }

    # 1. Get installation token
    token = get_installation_token(app_id, key_path, install_id)
    client = GitHubClient(token=token)

    # 2. Fetch PR info and diff
    pr = client.get_pull_request(event["repository"], event["number"])
    clone_url = pr["head"]["repo"]["clone_url"]
    head_ref = pr["head"]["ref"]
    diff_text = client.get_pull_request_diff(event["repository"], event["number"])

    # 3. Clone PR head into temp dir
    workdir = clone_pr_head(clone_url, head_ref, token=token)

    try:
        # 4. Run the analysis pipeline
        pkg = analyze_custom_diff(
            diff_text,
            repository=event["repository"],
            commit=event["head_sha"],
            pr_number=event["number"],
            pr_title=event["title"],
            source_root=os.path.join(workdir, "src"),
            tests_root=os.path.join(workdir, "tests"),
        )

        # 5. Post a check run back to the PR
        check = format_check(pkg)
        client.create_check_run(
            repo=event["repository"],
            name=check["name"],
            head_sha=event["head_sha"],
            conclusion=check["conclusion"],
            title=check["title"],
            summary=check["summary"],
            text=check["text"],
        )
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    return {"status": "processed", "evidence_id": pkg.id}
@app.get("/evidence/{evidence_id}")
def get_evidence(evidence_id: str) -> dict[str, Any]:
    import json
    path = os.path.join(DATA_DIR, f"{evidence_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="evidence not found")
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


@app.get("/evidence/{evidence_id}/json")
def get_evidence_json(evidence_id: str) -> dict[str, Any]:
    return get_evidence(evidence_id)