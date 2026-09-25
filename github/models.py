"""Pydantic models for GitHub webhook and API payloads."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class GitHubPRRef(BaseModel):
    number: int
    title: str = ""
    head_sha: str = ""
    base_sha: str = ""
    html_url: str = ""


class GitHubRepoRef(BaseModel):
    full_name: str
    clone_url: str = ""
    default_branch: str = "main"


class GitHubPRPayload(BaseModel):
    action: str
    number: int
    repository: GitHubRepoRef
    pull_request: GitHubPRRef
    raw: dict[str, Any] = {}


class CheckRunResult(BaseModel):
    id: Optional[int] = None
    url: Optional[str] = None
    conclusion: str = "neutral"