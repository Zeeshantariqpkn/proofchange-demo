"""GitHub webhook handler.

Validates the HMAC signature, extracts PR info, and returns a
structured payload the API can hand to the analysis pipeline.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any, Optional

from fastapi import Header, HTTPException, Request


def verify_signature(body: bytes, signature_header: str, secret: str) -> bool:
    if not signature_header or not isinstance(signature_header, str) or not secret:
        return False
    if not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    provided = signature_header.split("=", 1)[1]
    return hmac.compare_digest(expected, provided)


async def parse_github_webhook(
    request: Request,
    x_github_event: Optional[str] = Header(None),
    x_hub_signature_256: Optional[str] = Header(None),
) -> dict[str, Any]:
    secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "").strip()
    body = await request.body()

    # FastAPI may pass Header objects if defaults aren't resolved; normalize.
    event = x_github_event if isinstance(x_github_event, str) else None
    signature = (
        x_hub_signature_256 if isinstance(x_hub_signature_256, str) else None
    )

    # Fall back to reading directly from request headers if needed.
    if signature is None:
        signature = request.headers.get("X-Hub-Signature-256", "")
    if event is None:
        event = request.headers.get("X-GitHub-Event", "unknown")

    if secret:
        if not verify_signature(body, signature or "", secret):
            raise HTTPException(
                status_code=401, detail="invalid webhook signature"
            )

    try:
        payload = json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail=f"invalid JSON: {exc}") from exc

    return {
        "event": event or "unknown",
        "payload": payload,
    }


def extract_pr_event(
    event: str, payload: dict[str, Any]
) -> Optional[dict[str, Any]]:
    """Return a normalized PR event, or None if not a supported event."""
    if event != "pull_request":
        return None
    action = payload.get("action")
    if action not in ("opened", "synchronize", "reopened"):
        return None
    pr = payload.get("pull_request") or {}
    repo = payload.get("repository") or {}
    return {
        "action": action,
        "number": payload.get("number") or pr.get("number"),
        "title": pr.get("title", ""),
        "head_sha": (pr.get("head") or {}).get("sha", ""),
        "base_sha": (pr.get("base") or {}).get("sha", ""),
        "repository": (repo.get("full_name") or ""),
        "html_url": pr.get("html_url", ""),
    }