"""End-to-end: baseline -> improvement cycle -> gate -> promotion (mock LLM)."""
from backend.app.database import SessionLocal
from backend.app.graph.improvement_graph import run_experiment_sync
from backend.app.models import Candidate, Champion, Experiment
from backend.app.services import benchmark_service, promotion_service


def test_full_improvement_cycle():
    with SessionLocal() as db:
        champion = benchmark_service.run_baseline(db)
        assert champion.version == "0.1.0"
        baseline_score = champion.score
        exp = Experiment(objective="Improve the benchmark score")
        db.add(exp)
        db.commit()
        exp_id = exp.id

    result = run_experiment_sync(exp_id)

    with SessionLocal() as db:
        exp = db.get(Experiment, exp_id)
        assert exp.status == "AWAITING_APPROVAL", f"got {exp.status}: {exp.error}"
        assert exp.strategy == "hybrid_retrieval"
        cand = db.query(Candidate).filter_by(experiment_id=exp_id).one()
        assert cand.metrics["overall_score"] > baseline_score
        assert cand.decision["passed"]

        # Human gate: promotion only happens via explicit approval.
        new_champion = promotion_service.promote(db, cand, approved_by="test")
        assert new_champion.version == "0.2.0"
        assert new_champion.score > baseline_score

        active = db.query(Champion).filter_by(status="active").one()
        assert active.version == "0.2.0"
        assert db.get(Experiment, exp_id).status == "PROMOTED"
