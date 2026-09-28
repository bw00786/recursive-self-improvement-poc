"""Benchmark service: bootstrap the champion, run baselines, evaluate candidates."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from sqlalchemy.orm import Session

from ..audit import audit
from ..config import get_settings
from ..models import Candidate, Champion
from . import git_service, sandbox


def ensure_champion(db: Session) -> Champion:
    """Create champion v0.1.0 from the pristine sut/ tree if none exists."""
    champion = db.query(Champion).filter_by(status="active").first()
    if champion:
        return champion
    settings = get_settings()
    dest = settings.champion_dir / "v0.1.0"
    dest.mkdir(parents=True, exist_ok=True)
    if not (dest / "sut").exists():
        shutil.copytree(settings.sut_source_dir, dest / "sut",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    commit = git_service.commit_paths([dest], "champion v0.1.0: baseline")
    champion = Champion(
        version="0.1.0",
        sut_path=str(dest / "sut"),
        git_commit=commit,
        status="active",
        approved_by="bootstrap",
    )
    db.add(champion)
    db.commit()
    audit(db, "CHAMPION_BOOTSTRAPPED", version="0.1.0")
    return champion


def evaluate_sut_dir(sut_dir: Path) -> dict:
    """Direct in-process evaluation (bootstrap path)."""
    sys.path.insert(0, str(get_settings().repo_root))
    try:
        from benchmark.evaluator import evaluate
        return evaluate(sut_dir, get_settings().benchmark_dir / "benchmark.json")
    finally:
        sys.path.pop(0)


def run_baseline(db: Session) -> Champion:
    champion = ensure_champion(db)
    result = evaluate_sut_dir(Path(champion.sut_path))
    champion.metrics = result["metrics"]
    champion.score = result["metrics"]["overall_score"]
    db.commit()
    audit(db, "BASELINE_COMPLETED", version=champion.version, score=champion.score)
    return champion


def evaluate_candidate(db: Session, candidate: Candidate) -> dict:
    """Run the immutable benchmark against a candidate inside the sandbox."""
    result = sandbox.run_candidate_benchmark(Path(candidate.path))
    if not result.ok:
        candidate.status = "FAILED"
        db.commit()
        audit(db, "SANDBOX_FAILED", candidate=candidate.id, error=result.error)
        raise RuntimeError(f"sandbox failed: {result.error}\n{result.logs}")
    candidate.metrics = result.metrics
    candidate.status = "EVALUATED"
    db.commit()
    audit(db, "BENCHMARK_COMPLETED", candidate=candidate.id,
          score=result.metrics["overall_score"], isolated=result.isolated)
    return {"metrics": result.metrics, "items": result.items, "isolated": result.isolated}


def next_version(current: str) -> str:
    try:
        major, minor, patch = (int(x) for x in current.lstrip("v").split("."))
    except ValueError:
        return f"{current}-next"
    return f"{major}.{minor + 1}.0"
