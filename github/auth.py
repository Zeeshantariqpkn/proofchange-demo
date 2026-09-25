"""Generate a GitHub App installation access token."""
from __future__ import annotations

import time

import jwt
import requests


def _make_jwt(app_id: str, private_key_path: str) -> str:
    with open(private_key_path, "r", encoding="utf-8") as fh:
        private_key = fh.read()
    now = int(time.time())
    payload = {"iat": now - 60, "exp": now + 600, "iss": app_id}
    return jwt.encode(payload, private_key, algorithm="RS256")


def get_installation_token(app_id: str, private_key_path: str, installation_id: str) -> str:
    token = _make_jwt(app_id, private_key_path)
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    resp = requests.post(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()["token"]