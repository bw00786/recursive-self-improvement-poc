"""LangGraph nodes. Every node reads/writes the DB so the UI can follow along,
and every step is audited. Nodes return partial state updates."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from ..agents import analyst_agent, coder_agent, evaluator_agent, improvement_agent, researcher_agent
from ..audit import audit
from ..database import SessionLocal
from ..models import Candidate, Champion, Experiment
from ..services import benchmark_service, evaluation_service, promotion_service
from ..services.ollama import AgentLLM
from .state import ImprovementState


def _benchmark_fingerprint() -> str:
    """Hash the immutable benchmark so we can prove candidates didn't touch it."""
    from ..config import get_settings
    h = hashlib.sha256()
    for p in sorted(get_settings().benchmark_dir.glob("*")):
        if p.is_file():
            h.update(p.name.encode() + p.read_bytes())
    return h.hexdigest()


def _set_status(db, experiment_id: str, status: str) -> None:
    exp = db.get(Experiment, experiment_id)
    if exp:
        exp.status = status
        db.commit()


def load_champion(state: ImprovementState) -> dict:
    with SessionLocal() as db:
        champion = benchmark_service.ensure_champion(db)
        if not champion.metrics:
            benchmark_service.run_baseline(db)
            db.refresh(champion)
        _set_status(db, state["experiment_id"], "RUNNING")
        audit(db, "EXPERIMENT_STARTED", experiment=state["experiment_id"],
              champion=champion.version)
        return {
            "champion_version": champion.version,
            "champion_score": champion.score,
            "current_metrics": champion.metrics,
        }


def analyze_performance(state: ImprovementState) -> dict:
    llm = AgentLLM()
    analysis = analyst_agent.analyze(state["current_metrics"], None, llm)
    with SessionLocal() as db:
        audit(db, "ANALYSIS_COMPLETED", experiment=state["experiment_id"],
              weaknesses=len(analysis["weaknesses"]))
    return {"analysis": analysis, "failures": analysis["weaknesses"]}


def generate_hypothesis(state: ImprovementState) -> dict:
    llm = AgentLLM()
    with SessionLocal() as db:
        champion = db.query(Champion).filter_by(version=state["champion_version"]).one()
        hypothesis = improvement_agent.propose(db, champion, state["analysis"], llm)
        exp = db.get(Experiment, state["experiment_id"])
        exp.hypothesis = hypothesis
        exp.strategy = hypothesis.get("strategy")
        exp.status = "GENERATING"
        db.commit()
        audit(db, "HYPOTHESIS_GENERATED", experiment=exp.id,
              strategy=exp.strategy, hypothesis=hypothesis.get("hypothesis"))
    return {"hypothesis": hypothesis}


def research_solution(state: ImprovementState) -> dict:
    llm = AgentLLM()
    notes = researcher_agent.research(state["hypothesis"], llm)
    return {"research": notes}


def generate_candidate(state: ImprovementState) -> dict:
    llm = AgentLLM()
    with SessionLocal() as db:
        champion = db.query(Champion).filter_by(version=state["champion_version"]).one()
        exp = db.get(Experiment, state["experiment_id"])
        candidate = coder_agent.build_candidate(db, exp, state["hypothesis"], champion, llm)
        return {"candidate_id": candidate.id, "candidate_path": candidate.path}


def validate_candidate(state: ImprovementState) -> dict:
    """Security gate: diff candidate vs champion — every changed or new file
    must be in the candidate whitelist. (file_write content was already
    statically screened at creation time.)"""
    from .. import security
    ws = Path(state["candidate_path"])
    allowed_top = {"sut", "CHANGELOG.md", "PATCH_SUMMARY.md"}
    for item in ws.iterdir():
        if item.name not in allowed_top:
            raise security.SecurityViolation(f"unexpected file in candidate: {item.name}")

    with SessionLocal() as db:
        champion = db.query(Champion).filter_by(version=state["champion_version"]).one()
        base = Path(champion.sut_path)          # .../champion/vX/sut
        cand = ws / "sut"
        cand_files = {p.relative_to(cand) for p in cand.rglob("*")
                      if p.is_file() and "__pycache__" not in p.parts
                      and p.suffix != ".pyc"}
        base_files = {p.relative_to(base) for p in base.rglob("*")
                      if p.is_file() and "__pycache__" not in p.parts
                      and p.suffix != ".pyc"}
        for rel in sorted(cand_files | base_files):
            rel_str = f"sut/{rel.as_posix()}"
            c_file, b_file = cand / rel, base / rel
            changed = (
                not b_file.exists()
                or not c_file.exists()
                or c_file.read_bytes() != b_file.read_bytes()
            )
            if changed:
                # Must be whitelisted; raises SecurityViolation otherwise.
                security.validate_relative_path(rel_str)
        audit(db, "CANDIDATE_VALIDATED", candidate=state["candidate_id"])
    return {}


def run_sandbox(state: ImprovementState) -> dict:
    before = _benchmark_fingerprint()
    with SessionLocal() as db:
        candidate = db.get(Candidate, state["candidate_id"])
        _set_status(db, state["experiment_id"], "EVALUATING")
        result = benchmark_service.evaluate_candidate(db, candidate)
    after = _benchmark_fingerprint()
    if before != after:
        raise RuntimeError("benchmark mutated during candidate execution — rejecting")
    with SessionLocal() as db:
        audit(db, "SANDBOX_COMPLETED", candidate=state["candidate_id"],
              isolated=result["isolated"])
    return {"candidate_metrics": result["metrics"]}


def evaluate_candidate(state: ImprovementState) -> dict:
    with SessionLocal() as db:
        candidate = db.get(Candidate, state["candidate_id"])
        champion = db.query(Champion).filter_by(version=state["champion_version"]).one()
        evaluation_service.store_evaluations(db, candidate, state["candidate_metrics"], champion)
        audit(db, "EVALUATION_STORED", candidate=candidate.id)
    return {}


def compare_with_champion(state: ImprovementState) -> dict:
    with SessionLocal() as db:
        candidate = db.get(Candidate, state["candidate_id"])
        champion = db.query(Champion).filter_by(version=state["champion_version"]).one()
        decision = promotion_service.compare(state["candidate_metrics"], champion)
        candidate.decision = decision
        interpretation = evaluator_agent.interpret(state["candidate_metrics"], decision)
        if decision["passed"]:
            candidate.status = "AWAITING_APPROVAL"
            exp_status = "AWAITING_APPROVAL"
        else:
            candidate.status = "REJECTED"
            exp_status = "REJECTED"
        exp = db.get(Experiment, state["experiment_id"])
        exp.status = exp_status
        exp.result_score = decision["candidate_score"]
        exp.completed_at = datetime.now(timezone.utc)
        db.commit()
        return {
            "comparison": decision,
            "decision": "promote" if decision["passed"] else "reject",
            "approval_required": decision["requires_human_approval"],
            "interpretation": interpretation,
        }


def await_approval(state: ImprovementState) -> dict:
    with SessionLocal() as db:
        audit(db, "PROMOTION_REQUESTED", candidate=state["candidate_id"],
              delta=(state["comparison"] or {}).get("delta"))
    return {}


def record_failure(state: ImprovementState) -> dict:
    with SessionLocal() as db:
        exp = db.get(Experiment, state["experiment_id"])
        promotion_service.record_strategy(
            db, exp.strategy if exp else None,
            (state["comparison"] or {}).get("delta", 0.0), success=False)
        audit(db, "EXPERIMENT_REJECTED", experiment=state["experiment_id"],
              violations=(state["comparison"] or {}).get("hard_violations"))
    return {}
