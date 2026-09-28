"""Evaluator agent: human-readable interpretation of machine-computed results.

The DECISION is made by promotion_service (pure math). This agent only narrates.
"""
from __future__ import annotations


def interpret(metrics: dict, decision: dict) -> str:
    lines = [
        f"Candidate score: {decision['candidate_score']:.2f} "
        f"(champion {decision['champion_score']:.2f}, delta {decision['delta']:+.2f}).",
        f"accuracy={metrics.get('accuracy', 0):.2%}, "
        f"citation={metrics.get('citation_accuracy', 0):.2%}, "
        f"recall={metrics.get('retrieval_recall', 0):.2%}, "
        f"latency={metrics.get('latency_avg_s', 0):.2f}s.",
    ]
    if decision["hard_violations"]:
        lines.append("Hard violations: " + "; ".join(decision["hard_violations"]))
    if decision["passed"]:
        lines.append("Candidate passes all gates and awaits human approval.")
    else:
        lines.append("Candidate rejected by the promotion gate.")
    return "\n".join(lines)
