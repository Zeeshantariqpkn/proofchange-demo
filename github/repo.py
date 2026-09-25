"""Clone a GitHub repository at a specific ref."""
from __future__ import annotations

import os
import shutil
import tempfile

from git import Repo


def clone_pr_head(clone_url: str, ref: str, token: str = "") -> str:
    """Clone `clone_url` at `ref` into a fresh temp dir. Returns the path."""
    target = tempfile.mkdtemp(prefix="proofchange_")
    if token:
        authed = clone_url.replace("https://", f"https://x-access-token:{token}@")
    else:
        authed = clone_url

    if os.path.exists(target) and os.listdir(target):
        shutil.rmtree(target)
        os.makedirs(target)

    Repo.clone_from(authed, target, depth=1, branch=ref)
    return target