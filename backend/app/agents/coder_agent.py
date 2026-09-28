"""Coder agent: turn a hypothesis into a candidate workspace.

In real mode the LLM may emit its own modification list (validated against the
security whitelist); otherwise the hypothesis's validated modifications apply.
Either way, writes are confined to experiments/candidates/<id>/.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import Candidate, Champion, Experiment
from ..services import candidate_service
from ..services.ollama import AgentLLM


def build_candidate(db: Session, experiment: Experiment, hypothesis: dict,
                    champion: Champion, llm: AgentLLM) -> Candidate:
    if not llm.is_mock:
        resp = llm.complete_json(
            "You are the coding agent for an AI improvement system. Given this "
            f"hypothesis:\n{hypothesis}\n\nProduce the modification list that "
            "implements it. Allowed modification types:\n"
            '- {"type": "config_update", "updates": {<pipeline.yaml keys>}}\n'
            '- {"type": "prompt_update", "content": "<new system prompt>"}\n'
            "Return {\"modifications\": [...]}. Do not touch the evaluator or "
            "benchmark; only whitelisted config keys are permitted."
        )
        if resp and isinstance(resp.get("modifications"), list) and resp["modifications"]:
            hypothesis = {**hypothesis, "modifications": resp["modifications"]}
    return candidate_service.create_candidate(db, experiment, hypothesis, champion)
