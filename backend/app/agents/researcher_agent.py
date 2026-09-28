"""Researcher: attach implementation knowledge to a hypothesis.

No internet access in the POC — research is local (playbook knowledge + LLM
parametric knowledge when available).
"""
from __future__ import annotations

from ..services.ollama import AgentLLM

LOCAL_NOTES = {
    "hybrid_retrieval": [
        "Combine BM25 and vector rankings with reciprocal rank fusion (k=60).",
        "RRF needs no score normalization; it is robust to scale differences.",
    ],
    "query_rewriting": [
        "Rewrite the question into a declarative search query before retrieval.",
        "Keep the rewrite temperature at 0 for determinism.",
    ],
    "reranking": [
        "Rerank only the first-stage top-k; full-corpus cross-encoding is too slow.",
    ],
    "prompt_optimization": [
        "Explicit grounding instructions measurably improve citation behavior.",
    ],
    "context_tuning": [
        "Raising top_k improves recall but dilutes the context window; watch accuracy.",
    ],
}


def research(hypothesis: dict, llm: AgentLLM) -> list[str]:
    notes = list(LOCAL_NOTES.get(hypothesis.get("strategy", ""), []))
    if not llm.is_mock:
        resp = llm.complete(
            "Give two concise, implementation-relevant technical notes for this "
            f"improvement hypothesis:\n{hypothesis.get('hypothesis')}\n"
            f"Change: {hypothesis.get('proposed_change')}"
        )
        if resp.strip():
            notes.append(resp.strip()[:500])
    if not notes:
        notes.append("No specific prior art; rely on the benchmark to decide.")
    return notes
