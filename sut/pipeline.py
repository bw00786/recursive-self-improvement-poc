"""SUT pipeline: Question -> [rewrite] -> [retrieve] -> [rerank] -> LLM -> Answer.

Configuration lives in pipeline.yaml inside each champion/candidate directory,
so candidates improve the system by modifying configuration and code in their
own workspace — never the shared benchmark or evaluator.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .llm import get_llm
from .retrieval import Retriever

CITATION_RE = re.compile(r"\[source:\s*([^\]]+)\]")

DEFAULT_CONFIG = {
    "system_prompt": "You are a precise technical assistant.",
    "query_rewrite": False,
    "retrieval": "none",
    "rerank": False,
    "top_k": 4,
    "temperature": 0.0,
    "max_context_chars": 4000,
}


@dataclass
class PipelineResult:
    answer: str
    citations: list[str] = field(default_factory=list)
    retrieved: list[str] = field(default_factory=list)
    latency_ms: float = 0.0
    error: str | None = None


def load_config(sut_dir: str | Path) -> dict:
    cfg_path = Path(sut_dir) / "pipeline.yaml"
    cfg = dict(DEFAULT_CONFIG)
    if cfg_path.exists():
        cfg.update(yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {})
    return cfg


def run_pipeline(question: str, sut_dir: str | Path, llm=None) -> PipelineResult:
    sut_dir = Path(sut_dir)
    cfg = load_config(sut_dir)
    llm = llm or get_llm()
    start = time.perf_counter()
    try:
        query = question
        if cfg.get("query_rewrite"):
            rewritten = llm.complete(
                f"Rewrite this technical question as a precise search query. "
                f"Return only the query.\n\nQuestion: {question}",
                system="You are a query rewriting assistant.",
            ).strip()
            if rewritten:
                query = rewritten

        chunks = []
        if cfg.get("retrieval", "none") != "none":
            retriever = Retriever(sut_dir / "knowledge")
            chunks = retriever.search(query, mode=cfg["retrieval"], top_k=int(cfg.get("top_k", 4)))
            if cfg.get("rerank") and chunks:
                # Simple relevance rerank: prefer chunks sharing rare terms with the query.
                q_terms = set(re.findall(r"[a-z0-9]+", query.lower()))
                chunks = sorted(
                    chunks,
                    key=lambda c: len(q_terms & set(re.findall(r"[a-z0-9]+", c.text.lower()))),
                    reverse=True,
                )

        context = ""
        if chunks:
            max_chars = int(cfg.get("max_context_chars", 4000))
            context = "\n\n".join(f"=== Document: {c.doc} ===\n{c.text}" for c in chunks)[:max_chars]

        prompt = f"Question: {question}\n"
        if context:
            prompt += (
                f"\nUse ONLY the following context to answer, and cite every document "
                f"you use with [source: <name>].\n\n{context}\n"
            )
        system = cfg.get("system_prompt") or DEFAULT_CONFIG["system_prompt"]
        answer = llm.complete(prompt, system=system, temperature=float(cfg.get("temperature", 0.0)))
        latency = (time.perf_counter() - start) * 1000
        return PipelineResult(
            answer=answer,
            citations=CITATION_RE.findall(answer),
            retrieved=[c.doc for c in chunks],
            latency_ms=latency,
        )
    except Exception as exc:  # noqa: BLE001 — failures are a benchmark metric
        return PipelineResult(
            answer="", latency_ms=(time.perf_counter() - start) * 1000, error=str(exc)
        )
