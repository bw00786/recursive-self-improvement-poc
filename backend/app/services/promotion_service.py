"""Promotion gate: mathematical comparison + hard constraints + human approval.

A candidate is NEVER promoted because the LLM claims improvement. Promotion
requires: hard constraints pass, composite score beats the champion by a
configured margin, and explicit human approval (REQUIRE_HUMAN_APPROVAL).
"""
from __future__ import annotations

import shutil
from pathlib import Path

from sqlalchemy.orm import Session

from ..audit import audit
from ..config import get_settings
from ..models import Candidate, Champion, Experiment, StrategyStat
from . import benchmark_service, git_service


def compare(candidate_metrics: dict, champion: Champion) -> dict:
    """Return a structured promotion decision (passed, reasons, deltas)."""
    s = get_settings()
    base = champion.metrics or {}
    reasons: list[str] = []
    violations: list[str] = []

    # Hard constraints
    latency = candidate_metrics.get("latency_avg_s", 999.0)
    if latency > s.hard_max_latency_seconds:
        violations.append(f"latency {latency:.2f}s > hard max {s.hard_max_latency_seconds}s")
    if candidate_metrics.get("failure_rate", 1.0) > 0.0:
        violations.append(f"failure rate {candidate_metrics['failure_rate']:.2%} > 0")

    # Non-regression on quality metrics
    for m in ("accuracy", "citation_accuracy"):
        if candidate_metrics.get(m, 0.0) < base.get(m, 0.0) - 1e-6:
            violations.append(f"{m} regressed: {base.get(m, 0):.4f} -> "
                              f"{candidate_metrics.get(m, 0):.4f}")

    # Practically meaningful composite improvement
    cand_score = candidate_metrics.get("overall_score", 0.0)
    delta = cand_score - champion.score
    if delta < s.min_score_improvement:
        reasons.append(f"score delta {delta:+.2f} below required "
                       f"+{s.min_score_improvement}")

    passed = not violations and delta >= s.min_score_improvement
    return {
        "passed": passed,
        "hard_violations": violations,
        "reasons": reasons,
        "candidate_score": cand_score,
        "champion_score": champion.score,
        "delta": round(delta, 2),
        "requires_human_approval": s.require_human_approval,
    }


def record_strategy(db: Session, strategy: str | None, improvement: float,
                    success: bool) -> None:
    """Update learned strategy statistics — the recursive layer's memory."""
    if not strategy:
        return
    stat = db.get(StrategyStat, strategy)
    if stat is None:
        stat = StrategyStat(strategy=strategy, experiment_count=0,
                            success_count=0, success_rate=0.0,
                            average_improvement=0.0)
    prev_total = stat.average_improvement * stat.experiment_count
    stat.experiment_count += 1
    if success:
        stat.success_count += 1
    stat.success_rate = stat.success_count / stat.experiment_count
    stat.average_improvement = (prev_total + improvement) / stat.experiment_count
    db.add(stat)
    db.commit()


def promote(db: Session, candidate: Candidate, approved_by: str, reason: str = "") -> Champion:
    settings = get_settings()
    champion = db.query(Champion).filter_by(status="active").first()
    if champion is None:
        raise RuntimeError("no active champion")
    if candidate.status != "AWAITING_APPROVAL":
        raise RuntimeError(f"candidate {candidate.id} is not awaiting approval")

    new_version = benchmark_service.next_version(champion.version)
    dest = settings.champion_dir / f"v{new_version}"
    if dest.exists():
        shutil.rmtree(dest)  # idempotent re-promotion (e.g. after a crash)
    shutil.copytree(Path(candidate.path) / "sut", dest / "sut",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    commit = git_service.commit_paths([dest], f"champion v{new_version}: promote {candidate.id}")

    champion.status = "retired"
    new_champion = Champion(
        version=new_version,
        sut_path=str(dest / "sut"),
        git_commit=commit,
        score=candidate.metrics["overall_score"],
        metrics=candidate.metrics,
        status="active",
        approved_by=approved_by,
    )
    candidate.status = "PROMOTED"
    exp = db.get(Experiment, candidate.experiment_id)
    if exp:
        exp.status = "PROMOTED"
    db.add(new_champion)
    db.commit()
    record_strategy(db, exp.strategy if exp else None,
                    (candidate.decision or {}).get("delta", 0.0), success=True)
    audit(db, "CHAMPION_PROMOTED", version=new_version, candidate=candidate.id,
          approved_by=approved_by, reason=reason)
    return new_champion


def reject(db: Session, candidate: Candidate, approved_by: str, reason: str = "") -> None:
    candidate.status = "REJECTED"
    exp = db.get(Experiment, candidate.experiment_id)
    if exp:
        exp.status = "REJECTED"
    db.commit()
    record_strategy(db, exp.strategy if exp else None,
                    (candidate.decision or {}).get("delta", 0.0), success=False)
    audit(db, "CANDIDATE_REJECTED", candidate=candidate.id,
          approved_by=approved_by, reason=reason)
