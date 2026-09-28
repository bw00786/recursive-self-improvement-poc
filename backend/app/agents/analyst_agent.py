"""Analyst: identify weaknesses in the champion's benchmark results."""
from __future__ import annotations

from ..services.ollama import AgentLLM

THRESHOLDS = {
    "accuracy": 0.90,
    "citation_accuracy": 0.90,
    "retrieval_recall": 0.90,
    "reliability": 0.99,
    "latency_score": 0.5,
}


def analyze(metrics: dict, items: list[dict] | None, llm: AgentLLM) -> dict:
    weaknesses = [
        {"metric": m, "value": metrics.get(m, 0.0), "target": t}
        for m, t in THRESHOLDS.items()
        if metrics.get(m, 0.0) < t
    ]
    weaknesses.sort(key=lambda w: w["value"] - w["target"])

    worst_items: list[str] = []
    if items:
        worst = sorted(items, key=lambda i: i.get("accuracy", 1.0))[:5]
        worst_items = [i["id"] for i in worst if i.get("accuracy", 1.0) < 1.0]

    summary = ""
    if not llm.is_mock:
        resp = llm.complete_json(
            "You are a performance analyst for a retrieval QA system. "
            f"Metrics: {metrics}. Weaknesses: {weaknesses}. "
            'Return {"summary": "<one paragraph>"}.'
        )
        if resp and isinstance(resp.get("summary"), str):
            summary = resp["summary"]
    if not summary:
        if weaknesses:
            w = weaknesses[0]
            summary = (f"Primary weakness: {w['metric']} at {w['value']:.2f} "
                       f"(target {w['target']:.2f}).")
        else:
            summary = "All metrics meet targets; only incremental gains remain."
    return {"weaknesses": weaknesses, "worst_items": worst_items, "summary": summary}
