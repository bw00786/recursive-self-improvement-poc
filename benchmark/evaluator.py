"""Immutable benchmark evaluator — the gatekeeper.

This module lives OUTSIDE every candidate workspace. Candidates are executed
against it; they can never modify it. Runnable standalone:

    python benchmark/evaluator.py --sut experiments/champion/v0.1.0 \
        --benchmark benchmark/benchmark.json --out results.json

Use `--out -` to print the JSON result to stdout (used by the sandbox).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

CITATION_RE = re.compile(r"\[source:\s*([^\]]+)\]")

DEFAULT_WEIGHTS = {
    "accuracy": 0.40,
    "citation_accuracy": 0.25,
    "retrieval_recall": 0.20,
    "reliability": 0.10,
    "latency_score": 0.05,
}
LATENCY_FULL_CREDIT_S = 1.0
LATENCY_ZERO_CREDIT_S = 10.0


def _weights() -> dict[str, float]:
    raw = os.environ.get("EVAL_WEIGHTS")
    if raw:
        try:
            return {k: float(v) for k, v in json.loads(raw).items()}
        except Exception:
            pass
    return dict(DEFAULT_WEIGHTS)


def score_item(item: dict, answer: str, citations: list[str], retrieved: list[str]) -> dict:
    low = answer.lower()
    facts = item.get("expected_facts", [])
    hits = sum(1 for f in facts if f.lower() in low)
    accuracy = hits / len(facts) if facts else 0.0

    required = set(item.get("source_documents", []))
    cited = {c.strip() for c in citations}
    citation = len(required & cited) / len(required) if required else 1.0

    retrieved_set = set(retrieved)
    recall = len(required & retrieved_set) / len(required) if required else 1.0

    keywords = item.get("required_keywords", [])
    kw_hits = sum(1 for k in keywords if k.lower() in low)
    keyword_coverage = kw_hits / len(keywords) if keywords else 1.0

    return {
        "id": item["id"],
        "accuracy": round(accuracy, 4),
        "citation": round(citation, 4),
        "recall": round(recall, 4),
        "keyword_coverage": round(keyword_coverage, 4),
    }


def evaluate(sut_dir: str | Path, benchmark_path: str | Path, llm=None) -> dict:
    sut_dir = Path(sut_dir).resolve()
    # Import the SUT from the candidate workspace, never from the caller's path.
    # Evict any previously imported "sut" modules so each candidate is evaluated
    # against its own code, not a cached import from an earlier run.
    for mod in [m for m in list(sys.modules) if m == "sut" or m.startswith("sut.")]:
        del sys.modules[mod]
    sys.path.insert(0, str(sut_dir.parent))
    try:
        from sut.llm import get_llm  # noqa: WPS433
        from sut.pipeline import run_pipeline  # noqa: WPS433
    finally:
        sys.path.pop(0)
    if llm is None:
        llm = get_llm()

    items = json.loads(Path(benchmark_path).read_text(encoding="utf-8"))["items"]
    results, latencies, failures = [], [], 0
    for item in items:
        r = run_pipeline(item["question"], sut_dir, llm=llm)
        if r.error or not r.answer.strip():
            failures += 1
        results.append(score_item(item, r.answer, r.citations, r.retrieved))
        latencies.append(r.latency_ms)

    n = len(items) or 1
    accuracy = sum(r["accuracy"] for r in results) / n
    citation = sum(r["citation"] for r in results) / n
    recall = sum(r["recall"] for r in results) / n
    keyword_cov = sum(r["keyword_coverage"] for r in results) / n
    avg_latency_s = (sum(latencies) / n) / 1000.0
    failure_rate = failures / n
    reliability = 1.0 - failure_rate
    latency_score = max(
        0.0,
        min(1.0, (LATENCY_ZERO_CREDIT_S - avg_latency_s)
            / (LATENCY_ZERO_CREDIT_S - LATENCY_FULL_CREDIT_S)),
    )

    w = _weights()
    overall = 100.0 * (
        w.get("accuracy", 0.4) * accuracy
        + w.get("citation_accuracy", 0.25) * citation
        + w.get("retrieval_recall", 0.2) * recall
        + w.get("reliability", 0.1) * reliability
        + w.get("latency_score", 0.05) * latency_score
    )

    return {
        "metrics": {
            "accuracy": round(accuracy, 4),
            "citation_accuracy": round(citation, 4),
            "retrieval_recall": round(recall, 4),
            "keyword_coverage": round(keyword_cov, 4),
            "reliability": round(reliability, 4),
            "failure_rate": round(failure_rate, 4),
            "latency_avg_s": round(avg_latency_s, 3),
            "latency_score": round(latency_score, 4),
            "overall_score": round(overall, 2),
        },
        "items": results,
        "item_count": len(items),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sut", required=True, help="Path to champion/candidate SUT dir")
    ap.add_argument("--benchmark", required=True, help="Path to benchmark.json")
    ap.add_argument("--out", default="-", help="Output path, or '-' for stdout")
    args = ap.parse_args()
    result = evaluate(args.sut, args.benchmark)
    payload = json.dumps(result, indent=2)
    if args.out == "-":
        print(payload)
    else:
        Path(args.out).write_text(payload, encoding="utf-8")
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
