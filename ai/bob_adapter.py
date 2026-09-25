"""IBM Bob adapter.

Supports two modes:

- documented_bob_workflow (default): ProofChange runs the automated
  engine; Bob task prompts in ai/prompts.py are documented and used
  manually with IBM Bob.

- runtime_llm: if BOB_API_URL and BOB_API_KEY are configured,
  ProofChange calls the Bob inference API (OpenAI-compatible shape).
  If the endpoint is unavailable or wrong, it falls back cleanly.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Optional

import requests
from dotenv import load_dotenv

from ai import prompts

load_dotenv()


@dataclass
class BobResult:
    mode: str
    content: str
    provider: Optional[str] = None


class BobAdapter:
    def __init__(self) -> None:
        self.mode = os.environ.get("AI_MODE", "documented_bob_workflow").strip()
        self.api_url = os.environ.get("BOB_API_URL", "").strip()
        self.api_key = os.environ.get("BOB_API_KEY", "").strip()
        self.model = os.environ.get("BOB_MODEL", "bob-2.0").strip()

    @property
    def runtime_available(self) -> bool:
        return bool(
            self.mode == "runtime_llm"
            and self.api_url
            and self.api_key
        )

    def analyze_change(self, context: dict[str, Any]) -> BobResult:
        return self._run("repository_understanding", context)

    def detect_gaps(self, context: dict[str, Any]) -> BobResult:
        return self._run("test_gap_analysis", context)

    def generate_tests(self, context: dict[str, Any]) -> BobResult:
        return self._run("test_generation", context)

    def analyze_failure(self, context: dict[str, Any]) -> BobResult:
        return self._run("failure_analysis", context)

    def create_summary(self, context: dict[str, Any]) -> BobResult:
        return self._run("verification_summary", context)

    def _run(self, task: str, context: dict[str, Any]) -> BobResult:
        if not self.runtime_available:
            return BobResult(
                mode="documented_bob_workflow",
                content=self._documented_stub(task, context),
            )
        try:
            content = self._call_bob(task, context)
            return BobResult(
                mode="runtime_llm",
                content=content,
                provider=self.api_url,
            )
        except Exception as exc:
            return BobResult(
                mode="runtime_llm_failed",
                content=(
                    f"Bob API call failed: {exc}. "
                    "Falling back to documented Bob workflow."
                ),
            )

    def _documented_stub(self, task: str, context: dict[str, Any]) -> str:
        prompt = prompts.ALL_PROMPTS.get(task, "")
        return json.dumps(
            {
                "mode": "documented_bob_workflow",
                "task": task,
                "prompt": prompt,
                "note": (
                    "IBM Bob 2.0 is used as the documented AI development "
                    "partner for this task. See ai/prompts.py and "
                    "docs/bob-workflow.md."
                ),
            },
            indent=2,
        )

    def _call_bob(self, task: str, context: dict[str, Any]) -> str:
        system = prompts.ALL_PROMPTS.get(task, "")
        user = json.dumps(context, default=str, indent=2)

        url = self.api_url.rstrip("/") + "/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        if isinstance(data, dict) and "choices" in data:
            return data["choices"][0]["message"]["content"]
        if isinstance(data, dict) and "output" in data:
            return str(data["output"])
        return json.dumps(data, indent=2)