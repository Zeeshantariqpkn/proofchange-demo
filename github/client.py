"""Minimal GitHub REST client.

Uses a GitHub App installation token. Tokens are never hard-coded —
they are provided via environment variables or a token provider
callable. For the hackathon, the demo can run without any GitHub
credentials (Demo Mode).
"""
from __future__ import annotations

import os
from typing import Any, Optional

import requests


class GitHubClient:
    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or os.environ.get("GITHUB_TOKEN", "").strip()
        self.base = "https://api.github.com"

    @property
    def configured(self) -> bool:
        return bool(self.token)

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def get_pull_request(self, repo: str, pr_number: int) -> dict[str, Any]:
        url = f"{self.base}/repos/{repo}/pulls/{pr_number}"
        resp = requests.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_pull_request_files(self, repo: str, pr_number: int) -> list[dict[str, Any]]:
        url = f"{self.base}/repos/{repo}/pulls/{pr_number}/files"
        resp = requests.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_pull_request_diff(self, repo: str, pr_number: int) -> str:
        url = f"{self.base}/repos/{repo}/pulls/{pr_number}"
        headers = self._headers()
        headers["Accept"] = "application/vnd.github.v3.diff"
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.text

    def create_check_run(
        self,
        repo: str,
        *,
        name: str,
        head_sha: str,
        conclusion: str,
        title: str,
        summary: str,
        text: str = "",
        details_url: str = "",
    ) -> dict[str, Any]:
        url = f"{self.base}/repos/{repo}/check-runs"
        payload: dict[str, Any] = {
            "name": name,
            "head_sha": head_sha,
            "status": "completed",
            "conclusion": conclusion,
            "output": {
                "title": title,
                "summary": summary,
                "text": text,
            },
        }
        if details_url:
            payload["details_url"] = details_url
        resp = requests.post(url, headers=self._headers(), json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()