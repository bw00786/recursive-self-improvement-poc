"""MCP-compatible tool layer.

The improvement side of the system accesses capabilities through these
controlled tools — never through direct infrastructure access. Each tool has a
strict input schema, logging, audit, and error handling. Exposed over HTTP at
/api/mcp/* (a stdio MCP server can wrap the same registry later).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ..audit import audit
from ..database import SessionLocal
from ..models import AuditLog, Candidate, Champion, Evaluation, Experiment, StrategyStat


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict
    handler: Callable[..., Any]
    dangerous: bool = False


def _champion() -> dict:
    with SessionLocal() as db:
        c = db.query(Champion).filter_by(status="active").first()
        if not c:
            return {}
        return {"version": c.version, "score": c.score, "metrics": c.metrics}


def _experiment_history(limit: int = 20) -> list[dict]:
    with SessionLocal() as db:
        rows = (db.query(Experiment).order_by(Experiment.created_at.desc())
                .limit(min(limit, 100)).all())
        return [{"id": e.id, "strategy": e.strategy, "status": e.status,
                 "hypothesis": (e.hypothesis or {}).get("hypothesis"),
                 "result_score": e.result_score} for e in rows]


def _failures() -> list[dict]:
    with SessionLocal() as db:
        rows = (db.query(Experiment)
                .filter(Experiment.status.in_(["REJECTED", "FAILED"]))
                .order_by(Experiment.created_at.desc()).limit(50).all())
        return [{"id": e.id, "strategy": e.strategy, "status": e.status,
                 "error": e.error} for e in rows]


def _get_evaluation(candidate_id: str) -> list[dict]:
    with SessionLocal() as db:
        rows = (db.query(Evaluation).filter_by(candidate_id=candidate_id)
                .order_by(Evaluation.id).all())
        return [{"metric": r.metric_name, "value": r.metric_value,
                 "baseline": r.baseline_value, "delta": r.delta,
                 "passed": r.passed} for r in rows]


def _compare_candidate(candidate_id: str) -> dict:
    with SessionLocal() as db:
        c = db.get(Candidate, candidate_id)
        return (c.decision or {}) if c else {}


def _strategies() -> list[dict]:
    with SessionLocal() as db:
        return [{"strategy": s.strategy, "success_rate": s.success_rate,
                 "experiments": s.experiment_count,
                 "avg_improvement": s.average_improvement}
                for s in db.query(StrategyStat).all()]


def _audit_tail(limit: int = 20) -> list[dict]:
    with SessionLocal() as db:
        rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(min(limit, 100)).all()
        return [{"ts": r.ts.isoformat(), "event": r.event, "details": r.details}
                for r in rows]


TOOLS: dict[str, Tool] = {t.name: t for t in [
    Tool("get_champion", "Current champion version, score and metrics",
         {"type": "object", "properties": {}}, _champion),
    Tool("get_experiment_history", "Recent experiments with strategy and outcome",
         {"type": "object", "properties": {"limit": {"type": "integer", "default": 20}}},
         _experiment_history),
    Tool("get_failures", "Rejected/failed experiments for failure analysis",
         {"type": "object", "properties": {}}, _failures),
    Tool("get_evaluation", "Per-metric evaluation rows for a candidate",
         {"type": "object", "properties": {"candidate_id": {"type": "string"}},
          "required": ["candidate_id"]}, _get_evaluation),
    Tool("compare_candidate", "Promotion-gate decision for a candidate",
         {"type": "object", "properties": {"candidate_id": {"type": "string"}},
          "required": ["candidate_id"]}, _compare_candidate),
    Tool("get_strategies", "Learned strategy statistics (the recursive memory)",
         {"type": "object", "properties": {}}, _strategies),
    Tool("get_audit_log", "Recent audit events",
         {"type": "object", "properties": {"limit": {"type": "integer", "default": 20}}},
         _audit_tail),
]}


def list_tools() -> list[dict]:
    return [{"name": t.name, "description": t.description,
             "input_schema": t.input_schema} for t in TOOLS.values()]


def call_tool(name: str, arguments: dict) -> Any:
    tool = TOOLS.get(name)
    if not tool:
        raise KeyError(f"unknown tool: {name}")
    # Only schema-declared arguments are forwarded.
    allowed = set(tool.input_schema.get("properties", {}))
    kwargs = {k: v for k, v in (arguments or {}).items() if k in allowed}
    with SessionLocal() as db:
        audit(db, "MCP_TOOL_CALL", tool=name, arguments=kwargs)
    return tool.handler(**kwargs)
