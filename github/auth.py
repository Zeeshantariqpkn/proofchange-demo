"""Generate a GitHub App installation access token."""
from __future__ import annotations

import os
import time

import jwt
import requests


def _load_private_key() -> str:
    """Load the private key from env var (Streamlit Cloud) or file (local)."""
    # Streamlit Cloud: key stored as GITHUB_PRIVATE_KEY secret (newlines as \n)
    key_str = os.environ.get("GITHUB_PRIVATE_KEY", "").strip()
    if key_str:
        return key_str.replace("\\n", "\n")
    # Local: key stored as a .pem file path
    key_path = os.environ.get("GITHUB_PRIVATE_KEY_PATH", "").strip()
    if key_path and os.path.exists(key_path):
        with open(key_path, "r", encoding="utf-8") as fh:
            return fh.read()
    raise FileNotFoundError(
        "GitHub private key not found. Set GITHUB_PRIVATE_KEY (Streamlit Cloud) "
        "or GITHUB_PRIVATE_KEY_PATH pointing to a .pem file."
    )


def _make_jwt(app_id: str, private_key_path: str) -> str:
    private_key = _load_private_key()
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