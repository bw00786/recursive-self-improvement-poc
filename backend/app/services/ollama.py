"""LLM client for the improvement-side agents (analyst, researcher, coder...).

Falls back to a deterministic mock when Ollama is unreachable so the whole
improvement loop remains runnable and testable offline.
"""
from __future__ import annotations

import json
import re

import httpx

from ..config import get_settings

JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


class AgentLLM:
    def __init__(self):
        s = get_settings()
        self.base_url = s.ollama_base_url.rstrip("/")
        self.model = s.ollama_model
        mode = s.mock_llm.lower()
        if mode in ("true", "mock"):
            self.is_mock = True
        elif mode in ("false", "ollama"):
            self.is_mock = False
        else:
            self.is_mock = not self.reachable()

    def reachable(self) -> bool:
        try:
            with httpx.Client(timeout=3.0, trust_env=False) as client:
                return client.get(f"{self.base_url}/api/tags").status_code == 200
        except Exception:
            return False

    @property
    def name(self) -> str:
        return "mock" if self.is_mock else f"ollama:{self.model}"

    def complete(self, prompt: str, system: str | None = None) -> str:
        if self.is_mock:
            return ""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        }
        if system:
            payload["system"] = system
        with httpx.Client(timeout=240.0, trust_env=False) as client:
            resp = client.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json().get("response", "")

    def complete_json(self, prompt: str, system: str | None = None) -> dict | None:
        """Ask for JSON; return None on malformed output (callers reject/fallback)."""
        try:
            text = self.complete(prompt + "\n\nReturn ONLY valid JSON.", system=system)
        except Exception:
            return None
        m = JSON_BLOCK_RE.search(text or "")
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
