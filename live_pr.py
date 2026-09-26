"""Live GitHub PR analysis — invoked from the Streamlit app.

Uses the configured GitHub App credentials to fetch a real PR,
clone it, run the ProofChange pipeline, and optionally post a
Check Run back to GitHub.
"""
from __future__ import annotations

import os
import shutil
from typing import Any, Callable, Optional

from dotenv import load_dotenv

load_dotenv()


class LivePRError(Exception):
    """Raised when the live PR flow cannot proceed."""


def run_live_pr_analysis(
    repo: str,
    pr_number: int,
    post_check: bool = True,
    progress: Optional[Callable[[str], None]] = None,
) -> dict[str, Any]:
    """Run the ProofChange pipeline against a live GitHub PR.

    Parameters
    ----------
    repo : str
        Full repo name, e.g. "owner/repo".
    pr_number : int
        The PR number on GitHub.
    post_check : bool
        If True, post a Check Run back to the PR.
    progress : callable, optional
        Called with short status strings as the pipeline progresses.

    Returns
    -------
    dict
        The Change Evidence Package as a dict, plus:
        - "_pr_html_url": the PR's web URL
        - "_check_posted": bool
    """
    def _log(msg: str) -> None:
        if progress:
            progress(msg)

    # --- Validate configuration ---
    app_id = os.environ.get("GITHUB_APP_ID", "").strip()
    key_path = os.environ.get("GITHUB_PRIVATE_KEY_PATH", "").strip()
    install_id = os.environ.get("GITHUB_INSTALLATION_ID", "").strip()

    if not (app_id and key_path and install_id):
        raise LivePRError(
            "GitHub App credentials are not configured. "
            "Set GITHUB_APP_ID, GITHUB_PRIVATE_KEY_PATH, and "
            "GITHUB_INSTALLATION_ID in .env"
        )
    if not os.path.exists(key_path):
        raise LivePRError(f"Private key not found at {key_path}")

    # --- Lazy imports so the Streamlit app boots fast ---
    from github.auth import get_installation_token
    from github.checks import format_check
    from github.client import GitHubClient
    from github.repo import clone_pr_head
    from pipeline import analyze_custom_diff

    # --- 1. Get installation token ---
    _log("Authenticating with GitHub…")
    try:
        token = get_installation_token(app_id, key_path, install_id)
    except Exception as exc:
        raise LivePRError(f"GitHub authentication failed: {exc}") from exc

    client = GitHubClient(token=token)

    # --- 2. Fetch PR info and diff ---
    _log(f"Fetching PR #{pr_number} from {repo}…")
    try:
        pr = client.get_pull_request(repo, pr_number)
    except Exception as exc:
        raise LivePRError(f"Could not fetch PR: {exc}") from exc

    clone_url = pr["head"]["repo"]["clone_url"]
    head_ref = pr["head"]["ref"]
    head_sha = pr["head"]["sha"]
    title = pr.get("title", "")
    html_url = pr.get("html_url", "")

    _log("Fetching PR diff…")
    try:
        diff_text = client.get_pull_request_diff(repo, pr_number)
    except Exception as exc:
        raise LivePRError(f"Could not fetch PR diff: {exc}") from exc

    _log(f"Diff received ({len(diff_text)} chars)")

    # --- 3. Clone PR head into a temp folder ---
    _log(f"Cloning branch '{head_ref}' into temp folder…")
    try:
        workdir = clone_pr_head(clone_url, head_ref, token=token)
    except Exception as exc:
        raise LivePRError(f"Git clone failed: {exc}") from exc

    _log(f"Cloned to {workdir}")

    try:
        # --- 4. Run the pipeline ---
        _log("Running ProofChange pipeline…")
        pkg = analyze_custom_diff(
            diff_text,
            repository=repo,
            commit=head_sha,
            pr_number=pr_number,
            pr_title=title,
            source_root=os.path.join(workdir, "src"),
            tests_root=os.path.join(workdir, "tests"),
            repo_root=workdir,
        )
        result = pkg.to_dict()
        result["_pr_html_url"] = html_url
        result["_check_posted"] = False

        _log(
            f"Analysis complete. Evidence: "
            f"{result['evidence']['level']}  "
            f"({result['execution']['passed']}/{result['execution']['tests_executed']} tests passed)"
        )

        # --- 5. Optionally post a Check Run ---
        if post_check:
            _log("Posting Check Run to GitHub…")
            try:
                check = format_check(pkg)
                client.create_check_run(
                    repo=repo,
                    name=check["name"],
                    head_sha=head_sha,
                    conclusion=check["conclusion"],
                    title=check["title"],
                    summary=check["summary"],
                    text=check["text"],
                )
                result["_check_posted"] = True
                _log("Check Run posted ✅")
            except Exception as exc:
                _log(f"Check Run failed (non-fatal): {exc}")

        return result
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
        _log("Cleaned up temporary clone.")