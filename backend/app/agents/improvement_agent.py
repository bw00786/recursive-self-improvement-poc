"""Improvement agent (Llama 3.1): propose ONE measurable, reversible modification.

Structured output is validated; malformed LLM responses are rejected and the
deterministic playbook is used instead, so the loop can never be derailed by a
bad completion.
"""
from __future__ import annotations

from pathlib import Path

import yaml
from sqlalchemy.orm import Session

from ..models import Experiment, StrategyStat
from ..services.ollama import AgentLLM

REQUIRED_KEYS = {"hypothesis", "proposed_change", "expected_metric",
                 "expected_improvement", "modifications"}

STRONG_PROMPT = (
    "You are a precise technical assistant. Answer ONLY from the supplied "
    "context. Cite every document you use with [source: <name>]. If the "
    "context is insufficient, say so explicitly instead of guessing."
)


def _playbook(cfg: dict) -> list[dict]:
    """Candidate strategies in rough order of expected value, with preconditions."""
    return [
        {
            "strategy": "hybrid_retrieval",
            "applies": cfg.get("retrieval") != "hybrid",
            "hypothesis": "Hybrid retrieval (BM25 + vector with RRF) improves retrieval recall over the current configuration.",
            "proposed_change": "Enable hybrid retrieval mode.",
            "expected_metric": "retrieval_recall",
            "expected_improvement": 0.08,
            "risk": "slightly higher latency",
            "implementation_plan": ["set retrieval=hybrid", "benchmark"],
            "modifications": [{"type": "config_update",
                               "updates": {"retrieval": "hybrid", "top_k": 4}}],
        },
        {
            "strategy": "query_rewriting",
            "applies": not cfg.get("query_rewrite"),
            "hypothesis": "Query rewriting improves retrieval recall by aligning question phrasing with document vocabulary.",
            "proposed_change": "Add a query-rewriting step before retrieval.",
            "expected_metric": "retrieval_recall",
            "expected_improvement": 0.05,
            "risk": "one extra LLM call per question",
            "implementation_plan": ["set query_rewrite=true", "benchmark"],
            "modifications": [{"type": "config_update",
                               "updates": {"query_rewrite": True}}],
        },
        {
            "strategy": "reranking",
            "applies": cfg.get("retrieval") != "none" and not cfg.get("rerank"),
            "hypothesis": "A reranking stage improves top-of-list precision for the generator.",
            "proposed_change": "Enable reranking of retrieved chunks.",
            "expected_metric": "accuracy",
            "expected_improvement": 0.03,
            "risk": "added latency",
            "implementation_plan": ["set rerank=true", "benchmark"],
            "modifications": [{"type": "config_update", "updates": {"rerank": True}}],
        },
        {
            "strategy": "prompt_optimization",
            "applies": "Cite every document" not in str(cfg.get("system_prompt", "")),
            "hypothesis": "A stricter grounding prompt improves citation accuracy and reduces unsupported claims.",
            "proposed_change": "Replace the system prompt with explicit grounding + citation instructions.",
            "expected_metric": "citation_accuracy",
            "expected_improvement": 0.05,
            "risk": "more abstentions",
            "implementation_plan": ["update system_prompt", "benchmark"],
            "modifications": [{"type": "config_update",
                               "updates": {"system_prompt": STRONG_PROMPT}}],
        },
        {
            "strategy": "context_tuning",
            "applies": int(cfg.get("top_k", 4)) < 8,
            "hypothesis": "Retrieving more chunks with a larger context window raises recall on multi-fact questions.",
            "proposed_change": "Increase top_k to 6 and the context budget to 6000 chars.",
            "expected_metric": "retrieval_recall",
            "expected_improvement": 0.03,
            "risk": "longer prompts, more tokens",
            "implementation_plan": ["set top_k=6", "set max_context_chars=6000", "benchmark"],
            "modifications": [{"type": "config_update",
                               "updates": {"top_k": 6, "max_context_chars": 6000}}],
        },
    ]


def _champion_config(sut_path: str) -> dict:
    cfg_file = Path(sut_path) / "pipeline.yaml"
    return yaml.safe_load(cfg_file.read_text(encoding="utf-8")) if cfg_file.exists() else {}


def _validate(h: dict) -> bool:
    return (
        isinstance(h, dict)
        and REQUIRED_KEYS.issubset(h.keys())
        and isinstance(h["modifications"], list)
        and all(isinstance(m, dict) and "type" in m for m in h["modifications"])
        and isinstance(h.get("expected_improvement"), (int, float))
    )


def propose(db: Session, champion, analysis: dict, llm: AgentLLM) -> dict:
    cfg = _champion_config(champion.sut_path)
    tried = {e.strategy for e in db.query(Experiment).all() if e.strategy}
    stats = {s.strategy: s for s in db.query(StrategyStat).all()}

    # Real mode: ask Llama first; reject malformed output and fall back.
    if not llm.is_mock:
        resp = llm.complete_json(
            "You are an AI systems optimization engineer.\n\n"
            f"Current system config:\n{yaml.safe_dump(cfg)}\n"
            f"Champion metrics:\n{champion.metrics}\n"
            f"Observed weaknesses:\n{analysis.get('weaknesses')}\n"
            f"Strategies already tried: {sorted(tried)}\n"
            f"Strategy success rates: "
            f"{ {k: v.success_rate for k, v in stats.items()} }\n\n"
            "Propose ONE modification that could measurably improve the system.\n"
            "Constraints: do not modify the evaluator or benchmark; the change "
            "must be reversible; define a measurable success criterion.\n"
            'Schema: {"hypothesis": str, "proposed_change": str, "strategy": str, '
            '"expected_metric": str, "expected_improvement": number, "risk": str, '
            '"implementation_plan": [str], "modifications": '
            '[{"type": "config_update", "updates": {...}}]}\n'
            "Allowed config keys: system_prompt, query_rewrite, retrieval "
            "(none|keyword|vector|hybrid), rerank, top_k (1-20), temperature, "
            "max_context_chars."
        )
        if resp and _validate(resp):
            resp.setdefault("strategy", "llm_proposal")
            return resp

    # Deterministic fallback: first applicable untried strategy; otherwise the
    # historically most successful one that still applies.
    candidates = [p for p in _playbook(cfg) if p["applies"]]
    for p in candidates:
        if p["strategy"] not in tried:
            return dict(p)
    if candidates:
        candidates.sort(
            key=lambda p: stats.get(p["strategy"]).success_rate
            if p["strategy"] in stats else 0.0,
            reverse=True,
        )
        return dict(candidates[0])
    return {
        "strategy": "noop",
        "hypothesis": "No further configuration improvements are available.",
        "proposed_change": "none",
        "expected_metric": "overall_score",
        "expected_improvement": 0.0,
        "risk": "none",
        "implementation_plan": [],
        "modifications": [],
    }
