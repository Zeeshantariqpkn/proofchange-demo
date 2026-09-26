# ProofChange — CI/CD Integration Guide

ProofChange is built around a self-contained Python pipeline
([`pipeline.py`](../pipeline.py)) and a FastAPI server
([`api.py`](../api.py)).  Both can be wired into a CI/CD system with
minimal configuration.  This guide covers four integration patterns in
increasing order of complexity.

---

## Contents

1. [GitHub Actions — webhook-driven check runs](#1-github-actions--webhook-driven-check-runs)
2. [Local pre-commit hook](#2-local-pre-commit-hook)
3. [Standalone CLI](#3-standalone-cli)
4. [Exit codes and evidence levels](#4-exit-codes-and-evidence-levels)

---

## 1. GitHub Actions — webhook-driven check runs

### How it works

```
PR opened / updated
       │
       ▼
GitHub sends pull_request webhook
       │
       ▼
POST /webhooks/github  (api.py → github/webhook.py)
       │
       ├─ verify HMAC signature (github/webhook.py → verify_signature)
       ├─ clone PR head         (github/repo.py  → clone_pr_head)
       ├─ run full pipeline     (pipeline.py     → analyze_custom_diff)
       └─ post check run        (github/checks.py → format_check
                                 github/client.py → create_check_run)
```

The webhook handler lives at [`api.py:134`](../api.py#L134) and delegates
signature validation to [`github/webhook.py`](../github/webhook.py) and
check-run formatting to [`github/checks.py`](../github/checks.py).  The
three evidence levels map directly to GitHub check-run conclusions:

| Evidence level | GitHub conclusion | PR effect       |
|----------------|-------------------|-----------------|
| `STRONG`       | `success`         | check passes    |
| `PARTIAL`      | `neutral`         | check warns     |
| `INSUFFICIENT` | `failure`         | check fails     |

These mappings are defined in
[`github/checks.py:_conclusion_for()`](../github/checks.py#L10).

---

### Prerequisites

| What | Where to configure |
|------|--------------------|
| GitHub App with **Checks: write** and **Pull requests: read** permissions | GitHub → Settings → Developer Settings → GitHub Apps |
| App private key (`.pem` file) | stored as an Actions secret |
| Webhook secret (any random string) | same secret in App settings and in repo secrets |
| Installation ID | visible in `https://github.com/organizations/<org>/settings/installations` |

Store these four values as **repository secrets** (Settings → Secrets →
Actions):

```
GITHUB_APP_ID
GITHUB_PRIVATE_KEY          # full PEM content, not a path
GITHUB_INSTALLATION_ID
GITHUB_WEBHOOK_SECRET
```

---

### Running the server: two deployment strategies

**Option A — self-hosted runner (recommended for production)**

Run the Actions job on a runner that is reachable from the public
internet (or from GitHub's servers via a VPN / private network).  The
server listens on a stable hostname and GitHub can reach it directly.

**Option B — ephemeral tunnel (recommended for evaluation)**

Start the API server inside the Actions job, then expose it with a
public tunnel (e.g. [ngrok](https://ngrok.com) or
[Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)).
Register the tunnel URL as the webhook URL in the GitHub App settings
for the duration of the run.  This is the approach shown in the
workflow below.

> **Note:** The repository already ships an `ngrok-token.txt` for local
> demos.  In a real deployment, add your Ngrok auth token as the secret
> `NGROK_AUTHTOKEN` instead of committing the token.

---

### Complete workflow — `.github/workflows/proofchange.yml`

Create this file alongside the existing
[`.github/workflows/ci.yml`](../.github/workflows/ci.yml):

```yaml
# .github/workflows/proofchange.yml
#
# Starts the ProofChange API server, exposes it via an ngrok tunnel,
# registers the tunnel URL as the GitHub App webhook, and then waits
# for the webhook to fire and complete the check run.
#
# Secrets required:
#   GITHUB_APP_ID             - numeric App ID
#   GITHUB_PRIVATE_KEY        - full PEM content of the App private key
#   GITHUB_INSTALLATION_ID    - installation ID for this repository
#   GITHUB_WEBHOOK_SECRET     - shared secret for HMAC validation
#   NGROK_AUTHTOKEN           - ngrok auth token (option B only)

name: ProofChange — Change Verification

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  proofchange:
    runs-on: ubuntu-latest

    steps:
      # ── 1. Check out the code ─────────────────────────────────────────────
      - uses: actions/checkout@v4

      # ── 2. Set up Python ──────────────────────────────────────────────────
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      # ── 3. Install dependencies ───────────────────────────────────────────
      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt

      # ── 4. Write the App private key to a temp file ───────────────────────
      #    api.py reads GITHUB_PRIVATE_KEY_PATH (not the PEM directly).
      - name: Write GitHub App private key
        run: echo "${{ secrets.GITHUB_PRIVATE_KEY }}" > /tmp/proofchange.pem

      # ── 5. Start the ProofChange API server in the background ─────────────
      - name: Start API server
        env:
          GITHUB_APP_ID:            ${{ secrets.GITHUB_APP_ID }}
          GITHUB_PRIVATE_KEY_PATH:  /tmp/proofchange.pem
          GITHUB_INSTALLATION_ID:   ${{ secrets.GITHUB_INSTALLATION_ID }}
          GITHUB_WEBHOOK_SECRET:    ${{ secrets.GITHUB_WEBHOOK_SECRET }}
          AI_MODE:                  documented_bob_workflow   # no live LLM needed
        run: |
          uvicorn api:app --host 0.0.0.0 --port 8000 &
          # Wait until the health endpoint responds
          for i in $(seq 1 15); do
            curl -sf http://localhost:8000/health && break || sleep 2
          done

      # ── 6. Expose the server via ngrok (option B) ─────────────────────────
      #    Skip this step if you use a self-hosted runner with a stable URL.
      - name: Install ngrok
        run: |
          curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
            | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
          echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
            | sudo tee /etc/apt/sources.list.d/ngrok.list
          sudo apt-get update -q && sudo apt-get install -yq ngrok

      - name: Start ngrok tunnel
        run: |
          ngrok authtoken ${{ secrets.NGROK_AUTHTOKEN }}
          ngrok http 8000 --log=stdout &
          sleep 5
          # Extract the public HTTPS URL from ngrok's local API
          TUNNEL_URL=$(curl -s http://localhost:4040/api/tunnels \
            | python3 -c "import sys,json; \
                          d=json.load(sys.stdin); \
                          print(d['tunnels'][0]['public_url'])")
          echo "TUNNEL_URL=${TUNNEL_URL}" >> "$GITHUB_ENV"
          echo "Webhook URL: ${TUNNEL_URL}/webhooks/github"

      # ── 7. Update the GitHub App webhook URL ──────────────────────────────
      #    Uses the GitHub API to point the App's webhook at the tunnel.
      #    Requires the App to have been created with a placeholder URL.
      - name: Update webhook URL
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          curl -sf -X PATCH \
            -H "Authorization: Bearer ${GH_TOKEN}" \
            -H "Accept: application/vnd.github+json" \
            "https://api.github.com/app/hook/config" \
            -d "{\"url\":\"${TUNNEL_URL}/webhooks/github\",\
                 \"content_type\":\"json\",\
                 \"secret\":\"${{ secrets.GITHUB_WEBHOOK_SECRET }}\"}"

      # ── 8. Trigger the webhook by re-requesting a delivery ────────────────
      #    GitHub re-delivers the pull_request event so the server processes it
      #    without needing a second commit.
      - name: Trigger ProofChange analysis
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # Re-deliver the most recent pull_request webhook delivery
          DELIVERY_ID=$(curl -sf \
            -H "Authorization: Bearer ${GH_TOKEN}" \
            -H "Accept: application/vnd.github+json" \
            "https://api.github.com/app/hook/deliveries?per_page=5" \
            | python3 -c "import sys,json; \
                          ds=json.load(sys.stdin); \
                          pr=[d for d in ds if d['event']=='pull_request']; \
                          print(pr[0]['id']) if pr else print('')")
          if [ -n "${DELIVERY_ID}" ]; then
            curl -sf -X POST \
              -H "Authorization: Bearer ${GH_TOKEN}" \
              -H "Accept: application/vnd.github+json" \
              "https://api.github.com/app/hook/deliveries/${DELIVERY_ID}/attempts"
          fi
          # Give the server time to process and post the check run
          sleep 15

      # ── 9. Poll the check run result and set the job exit code ───────────
      #    INSUFFICIENT → exit 1 (fails the PR).
      #    PARTIAL      → exit 0 (check passes with a warning in the UI).
      #    STRONG       → exit 0.
      - name: Evaluate evidence level
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          REPO:     ${{ github.repository }}
          SHA:      ${{ github.event.pull_request.head.sha }}
        run: |
          CONCLUSION=$(curl -sf \
            -H "Authorization: Bearer ${GH_TOKEN}" \
            -H "Accept: application/vnd.github+json" \
            "https://api.github.com/repos/${REPO}/commits/${SHA}/check-runs" \
            | python3 -c "import sys,json; \
                          runs=json.load(sys.stdin)['check_runs']; \
                          pc=[r for r in runs \
                              if r['name'].startswith('ProofChange')]; \
                          print(pc[0]['conclusion'] if pc else 'none')")
          echo "ProofChange conclusion: ${CONCLUSION}"
          if [ "${CONCLUSION}" = "failure" ]; then
            echo "::error::ProofChange evidence is INSUFFICIENT. \
Add tests covering the changed code before merging."
            exit 1
          fi
```

---

### Simpler alternative: run the pipeline directly (no webhook)

If you do not need GitHub Check Runs and just want to block the PR on
evidence level, call `pipeline.py` directly without starting a server:

```yaml
# Minimal step — add after checkout + pip install
- name: Run ProofChange
  env:
    AI_MODE: documented_bob_workflow
  run: |
    python - <<'EOF'
    import sys
    from pipeline import analyze_custom_diff
    import subprocess, os

    diff = subprocess.check_output(
        ["git", "diff", "origin/main...HEAD"], text=True
    )
    pkg = analyze_custom_diff(
        diff,
        repository=os.environ.get("GITHUB_REPOSITORY", ""),
        commit=os.environ.get("GITHUB_SHA", ""),
        pr_number=int(os.environ.get("GITHUB_REF_NAME", "0").split("/")[0] or 0),
        source_root="src",
        tests_root="tests",
    )
    level = pkg.evidence["level"]
    print(f"Evidence: {level}")
    if level == "INSUFFICIENT":
        sys.exit(1)
    EOF
```

This approach uses [`pipeline.analyze_custom_diff()`](../pipeline.py#L156)
directly and exits with code `1` when evidence is `INSUFFICIENT`, failing
the workflow step and blocking the PR merge.

---

## 2. Local pre-commit hook

Run ProofChange before every `git push` to catch evidence gaps before
they reach the remote.

### Setup

```bash
# From the repo root
cat > .git/hooks/pre-push << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

# Resolve the upstream branch (default: origin/main)
UPSTREAM="${PROOFCHANGE_BASE:-origin/main}"

echo "[proofchange] Comparing HEAD against ${UPSTREAM}…"

# Generate the diff between the upstream base and local HEAD
DIFF=$(git diff "${UPSTREAM}...HEAD" -- '*.py' 2>/dev/null || true)

if [ -z "${DIFF}" ]; then
  echo "[proofchange] No Python changes detected — skipping."
  exit 0
fi

# Run the analysis inline via Python
python3 - <<PYEOF
import sys, os
sys.path.insert(0, "$(git rev-parse --show-toplevel)")
os.chdir("$(git rev-parse --show-toplevel)")

diff_text = """${DIFF}"""

from pipeline import analyze_custom_diff
pkg = analyze_custom_diff(
    diff_text,
    source_root="src",
    tests_root="tests",
)

level = pkg.evidence["level"]
rationale = pkg.evidence["rationale"]

print(f"\n[proofchange] Evidence: {level}")
print(f"[proofchange] {rationale}")

if level == "INSUFFICIENT":
    print("\n[proofchange] Push blocked — add tests before pushing.")
    sys.exit(1)
elif level == "PARTIAL":
    print("[proofchange] Warning — consider improving test coverage.")
PYEOF
EOF

chmod +x .git/hooks/pre-push
```

### Behaviour

| Evidence | Hook action                          |
|----------|--------------------------------------|
| `STRONG` | push proceeds silently               |
| `PARTIAL`| warning printed, push proceeds       |
| `INSUFFICIENT` | push blocked, exit 1          |

To bypass in an emergency:

```bash
git push --no-verify
```

To share the hook across the team, commit it to `.githooks/pre-push` and
instruct developers to run:

```bash
git config core.hooksPath .githooks
```

---

## 3. Standalone CLI

The [`pipeline.py`](../pipeline.py) module exposes everything needed for
a thin CLI wrapper.  The hypothetical command below is not yet
implemented as a script, but the following shows exactly how it would
be built on top of `analyze_custom_diff`.

### Hypothetical `proofchange analyze --pr 123`

```python
#!/usr/bin/env python3
"""proofchange — CLI entry point.

Usage:
    proofchange analyze --pr <number> [--repo <owner/repo>] [--base <ref>]
    proofchange analyze --diff <file>  [--source <dir>] [--tests <dir>]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import os

# Add the repo root to sys.path when invoked directly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import analyze_custom_diff   # pipeline.py


EXIT_STRONG       = 0
EXIT_PARTIAL      = 0   # warning only — does not block CI
EXIT_INSUFFICIENT = 1


def _fetch_diff_from_github(repo: str, pr_number: int) -> str:
    """Fetch the raw unified diff for a PR using the GitHub REST API."""
    import urllib.request
    token = os.environ.get("GITHUB_TOKEN", "")
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github.v3.diff",
        "Authorization": f"Bearer {token}",
    })
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(prog="proofchange")
    sub = parser.add_subparsers(dest="command")

    analyze = sub.add_parser("analyze", help="Analyze a PR or diff file")
    analyze.add_argument("--pr",     type=int,   help="PR number to analyze")
    analyze.add_argument("--repo",   default="", help="owner/repo (required with --pr)")
    analyze.add_argument("--base",   default="origin/main",
                         help="Base ref for local diff (default: origin/main)")
    analyze.add_argument("--diff",   help="Path to a unified diff file")
    analyze.add_argument("--source", default="src",   help="Source root directory")
    analyze.add_argument("--tests",  default="tests", help="Tests root directory")
    analyze.add_argument("--fail-on", choices=["INSUFFICIENT", "PARTIAL"],
                         default="INSUFFICIENT",
                         help="Minimum evidence level that fails the command")

    args = parser.parse_args()

    if args.command != "analyze":
        parser.print_help()
        sys.exit(0)

    # ── Obtain the diff ───────────────────────────────────────────────────
    if args.pr:
        if not args.repo:
            # Try $GITHUB_REPOSITORY set by Actions
            args.repo = os.environ.get("GITHUB_REPOSITORY", "")
        if not args.repo:
            print("error: --repo is required when using --pr", file=sys.stderr)
            sys.exit(2)
        diff_text = _fetch_diff_from_github(args.repo, args.pr)
        pr_number = args.pr
    elif args.diff:
        with open(args.diff, "r", encoding="utf-8") as fh:
            diff_text = fh.read()
        pr_number = None
    else:
        # Fall back to a local git diff
        diff_text = subprocess.check_output(
            ["git", "diff", f"{args.base}...HEAD"], text=True
        )
        pr_number = None

    # ── Run the pipeline ─────────────────────────────────────────────────
    pkg = analyze_custom_diff(
        diff_text,
        repository=args.repo,
        pr_number=pr_number,
        source_root=args.source,
        tests_root=args.tests,
    )

    level     = pkg.evidence["level"]
    rationale = pkg.evidence["rationale"]

    print(f"Evidence:  {level}")
    print(f"Rationale: {rationale}")
    print(f"Files changed:      {pkg.change['files_changed']}")
    print(f"Functions affected: {pkg.change['functions_affected']}")
    print(f"Gaps detected:      {pkg.testing['test_gaps']}")
    print(f"Tests executed:     {pkg.execution['tests_executed']}")
    print(f"Passed:             {pkg.execution['passed']}")

    should_fail = (
        level == "INSUFFICIENT"
        or (args.fail_on == "PARTIAL" and level == "PARTIAL")
    )
    sys.exit(EXIT_INSUFFICIENT if should_fail else EXIT_STRONG)


if __name__ == "__main__":
    main()
```

Save this as `proofchange_cli.py` (or wire it into `setup.py` as a
`console_scripts` entry point) and invoke it as:

```bash
# Analyze a real GitHub PR
GITHUB_TOKEN=ghp_... python proofchange_cli.py analyze --pr 42 --repo owner/repo

# Analyze a local diff file
python proofchange_cli.py analyze --diff my_changes.diff --source src --tests tests

# Fail on PARTIAL as well (strict mode)
python proofchange_cli.py analyze --pr 42 --repo owner/repo --fail-on PARTIAL
```

---

## 4. Exit codes and evidence levels

All three integration patterns above converge on the same three evidence
levels produced by
[`engine/evidence.py:_compute_level()`](../engine/evidence.py#L30):

### Level definitions

| Level          | Meaning | Recommended CI action |
|----------------|---------|----------------------|
| `STRONG`       | All tests passed; every detected gap is targeted by a generated test; ≥ 70 % of analyzed code paths are verified. | ✅ Allow merge |
| `PARTIAL`      | Tests passed, but some gaps remain or path coverage is below 70 %. | ⚠️ Warn; allow merge at team discretion |
| `INSUFFICIENT` | No tests were executed **or** at least one test failed. | ❌ Block merge |

### Decision logic (from [`engine/evidence.py`](../engine/evidence.py))

```
if execution.total == 0          → INSUFFICIENT ("No tests were executed")
if execution.failed > 0          → INSUFFICIENT ("<n> test(s) failed")
if any high-severity gap remains → PARTIAL
if any gap remains OR
   verified_paths / analyzed_paths < 0.70 → PARTIAL
otherwise                        → STRONG
```

### GitHub check-run conclusions (from [`github/checks.py`](../github/checks.py))

```python
"STRONG"       → conclusion: "success"   # green tick
"PARTIAL"      → conclusion: "neutral"   # grey dot
"INSUFFICIENT" → conclusion: "failure"   # red cross  ← blocks merge
                                                         when branch
                                                         protection is on
```

### Mapping to standard exit codes

| Evidence | Recommended exit code | Rationale |
|----------|-----------------------|-----------|
| `STRONG`       | `0` | CI passes unconditionally |
| `PARTIAL`      | `0` | Warn but do not break the build; enforce via branch protection rules instead |
| `INSUFFICIENT` | `1` | Hard failure — no execution evidence or tests broke |

To treat `PARTIAL` as a hard failure (strict mode), exit with `1` for
both `PARTIAL` and `INSUFFICIENT`.  This is exposed as `--fail-on
PARTIAL` in the CLI above and can be set via an environment variable in
the Actions workflow:

```yaml
env:
  PROOFCHANGE_FAIL_ON: PARTIAL   # set to INSUFFICIENT for lenient mode
```

---

## Environment variables reference

All secrets are read from environment variables.  See
[`.env.example`](../.env.example) for local development defaults.

| Variable                  | Used in                          | Description |
|---------------------------|----------------------------------|-------------|
| `GITHUB_APP_ID`           | `api.py`, `github/auth.py`       | Numeric GitHub App ID |
| `GITHUB_PRIVATE_KEY_PATH` | `api.py`, `github/auth.py`       | Path to `.pem` private key file |
| `GITHUB_INSTALLATION_ID`  | `api.py`, `github/auth.py`       | Installation ID for this repository |
| `GITHUB_WEBHOOK_SECRET`   | `github/webhook.py`              | HMAC secret for signature validation |
| `AI_MODE`                 | `ai/bob_adapter.py`              | `documented_bob_workflow` (no LLM) or `runtime_llm` |
| `AI_PROVIDER_BASE_URL`    | `ai/bob_adapter.py`              | Base URL of the LLM endpoint |
| `AI_PROVIDER_API_KEY`     | `ai/bob_adapter.py`              | API key for the LLM provider |
| `AI_MODEL`                | `ai/bob_adapter.py`              | Model name (e.g. `ibm-bob-2.0`) |
| `PROOFCHANGE_DATA_DIR`    | `api.py`                         | Directory for evidence JSON files (default: `./data`) |
| `PROOFCHANGE_OUTPUT_DIR`  | `api.py`                         | Directory for generated output (default: `./output`) |
