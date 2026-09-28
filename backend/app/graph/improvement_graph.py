"""The improvement loop as a LangGraph state machine.

START -> load_champion -> analyze_performance -> generate_hypothesis
      -> research_solution -> generate_candidate -> validate_candidate
      -> run_sandbox -> evaluate_candidate -> compare_with_champion
      -> passed: await_approval -> END   (human gate via REST API)
      -> failed: record_failure -> END
"""
from __future__ import annotations

from datetime import datetime, timezone

from langgraph.graph import END, START, StateGraph

from ..audit import audit
from ..database import SessionLocal
from ..models import Experiment
from . import nodes
from .state import ImprovementState


def build_graph():
    g = StateGraph(ImprovementState)
    g.add_node("load_champion", nodes.load_champion)
    g.add_node("analyze_performance", nodes.analyze_performance)
    g.add_node("generate_hypothesis", nodes.generate_hypothesis)
    g.add_node("research_solution", nodes.research_solution)
    g.add_node("generate_candidate", nodes.generate_candidate)
    g.add_node("validate_candidate", nodes.validate_candidate)
    g.add_node("run_sandbox", nodes.run_sandbox)
    g.add_node("evaluate_candidate", nodes.evaluate_candidate)
    g.add_node("compare_with_champion", nodes.compare_with_champion)
    g.add_node("await_approval", nodes.await_approval)
    g.add_node("record_failure", nodes.record_failure)

    g.add_edge(START, "load_champion")
    g.add_edge("load_champion", "analyze_performance")
    g.add_edge("analyze_performance", "generate_hypothesis")
    g.add_edge("generate_hypothesis", "research_solution")
    g.add_edge("research_solution", "generate_candidate")
    g.add_edge("generate_candidate", "validate_candidate")
    g.add_edge("validate_candidate", "run_sandbox")
    g.add_edge("run_sandbox", "evaluate_candidate")
    g.add_edge("evaluate_candidate", "compare_with_champion")
    g.add_conditional_edges(
        "compare_with_champion",
        lambda s: "await_approval" if s.get("decision") == "promote" else "record_failure",
        {"await_approval": "await_approval", "record_failure": "record_failure"},
    )
    g.add_edge("await_approval", END)
    g.add_edge("record_failure", END)
    return g.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def run_experiment_sync(experiment_id: str) -> dict:
    """Execute one full improvement cycle. Runs in a worker thread."""
    initial: ImprovementState = {
        "experiment_id": experiment_id,
        "objective": "Improve the benchmark score",
        "approval_required": True,
    }
    try:
        return get_graph().invoke(initial)
    except Exception as exc:  # noqa: BLE001 — failures must be recorded, not lost
        with SessionLocal() as db:
            exp = db.get(Experiment, experiment_id)
            if exp:
                exp.status = "FAILED"
                exp.error = str(exc)[:4000]
                exp.completed_at = datetime.now(timezone.utc)
                db.commit()
            audit(db, "EXPERIMENT_FAILED", experiment=experiment_id, error=str(exc)[:1000])
        return {"decision": "failed", "error": str(exc)}
