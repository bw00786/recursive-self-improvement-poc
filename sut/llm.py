"""LLM access for the SUT. Supports Ollama (Llama 3.1) and a deterministic mock.

The mock mode exists so the entire improvement loop is reproducible offline:
the mock can only answer correctly when retrieval supplies the right context,
which makes retrieval improvements measurable.
"""
from __future__ import annotations

import os
import re

import httpx

DOC_HEADER_RE = re.compile(r"=== Document: (.+?) ===")


class OllamaLLM:
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.model = model or os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
        self.name = f"ollama:{self.model}"

    def complete(self, prompt: str, system: str | None = None, temperature: float = 0.0) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system
        with httpx.Client(timeout=180.0, trust_env=False) as client:
            resp = client.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json().get("response", "")

    def reachable(self) -> bool:
        try:
            with httpx.Client(timeout=3.0, trust_env=False) as client:
                return client.get(f"{self.base_url}/api/tags").status_code == 200
        except Exception:
            return False


class MockLLM:
    """Deterministic offline LLM. Answers purely from supplied context."""

    name = "mock"

    def complete(self, prompt: str, system: str | None = None, temperature: float = 0.0) -> str:
        sections = re.split(r"(=== Document: .+? ===)", prompt)
        docs: list[tuple[str, str]] = []
        for i in range(1, len(sections) - 1, 2):
            m = DOC_HEADER_RE.match(sections[i])
            if m:
                docs.append((m.group(1), sections[i + 1].strip()))
        if not docs:
            return (
                "I do not have enough information in my context to answer this "
                "question reliably."
            )
        parts = ["Based on the knowledge base:"]
        for name, text in docs:
            snippet = " ".join(text.split())[:600]
            parts.append(f"\n- ({name}) {snippet}")
        parts.append("\nSources: " + " ".join(f"[source: {name}]" for name, _ in docs))
        return "\n".join(parts)


def get_llm() -> OllamaLLM | MockLLM:
    mode = os.environ.get("SUT_LLM", os.environ.get("MOCK_LLM", "auto")).lower()
    if mode in ("true", "mock"):
        return MockLLM()
    llm = OllamaLLM()
    if mode in ("false", "ollama"):
        return llm
    return llm if llm.reachable() else MockLLM()
