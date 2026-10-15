"""Benchmark service: bootstrap the champion, run baselines, evaluate candidates."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from sqlalchemy.orm import Session

from ..audit import audit
from ..config import get_settings
from ..models import Candidate, Champion
from . import git_service, sandbox

# Per-question benchmark results, stored next to sut/ in champion and candidate dirs.
RESULTS_FILE = "results.json"


def _save_items(root: Path, items: list) -> None:
    (root / RESULTS_FILE).write_text(json.dumps(items, indent=1), encoding="utf-8")


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
    _save_items(Path(champion.sut_path).parent, result["items"])
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
    _save_items(Path(candidate.path), result.items)
    audit(db, "BENCHMARK_COMPLETED", candidate=candidate.id,
          score=result.metrics["overall_score"], isolated=result.isolated)
    return {"metrics": result.metrics, "items": result.items, "isolated": result.isolated}


def champion_items(champion: Champion) -> list[dict]:
    """Per-question results for the champion; benchmarks it once if not cached."""
    root = Path(champion.sut_path).parent
    cached = root / RESULTS_FILE
    if cached.exists():
        return json.loads(cached.read_text(encoding="utf-8"))
    result = sandbox.run_candidate_benchmark(root)
    if not result.ok:
        raise RuntimeError(f"champion benchmark failed: {result.error}")
    _save_items(root, result.items)
    return result.items


def champion_misses(champion: Champion, limit: int = 5) -> list[dict]:
    """Benchmark questions the champion does not fully get right, worst first."""
    bench_file = get_settings().benchmark_dir / "benchmark.json"
    questions = {q["id"]: q for q in json.loads(bench_file.read_text(encoding="utf-8"))["items"]}
    misses = []
    for r in champion_items(champion):
        if min(r["accuracy"], r["citation"], r["recall"]) >= 1.0:
            continue
        q = questions.get(r["id"], {})
        misses.append({
            "id": r["id"],
            "question": q.get("question"),
            "expected_facts": q.get("expected_facts"),
            "missing_facts": r.get("missing_facts"),
            "source_documents": q.get("source_documents"),
            "accuracy": r["accuracy"],
            "citation": r["citation"],
            "recall": r["recall"],
            "answer": r.get("answer"),
        })
    misses.sort(key=lambda m: m["accuracy"] + m["citation"] + m["recall"])
    return misses[:limit]


def next_version(current: str) -> str:
    try:
        major, minor, patch = (int(x) for x in current.lstrip("v").split("."))
    except ValueError:
        return f"{current}-next"
    return f"{major}.{minor + 1}.0"
