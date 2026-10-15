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
        # Per-question results travel with the promoted champion.
        assert benchmark_service.champion_items(active)


def test_no_new_ideas_skips_benchmark(monkeypatch):
    from backend.app.agents import improvement_agent

    monkeypatch.setattr(improvement_agent, "propose", lambda *a, **k: {
        "strategy": "noop", "hypothesis": "none", "proposed_change": "none",
        "expected_metric": "overall_score", "expected_improvement": 0.0,
        "modifications": []})
    with SessionLocal() as db:
        exp = Experiment(objective="Improve the benchmark score")
        db.add(exp)
        db.commit()
        exp_id = exp.id

    run_experiment_sync(exp_id)

    with SessionLocal() as db:
        exp = db.get(Experiment, exp_id)
        assert exp.status == "FAILED"
        assert exp.error.startswith("No new ideas")
        assert db.query(Candidate).filter_by(experiment_id=exp_id).count() == 0


def test_champion_misses_lists_failing_questions(tmp_path):
    import json
    (tmp_path / "sut").mkdir()
    (tmp_path / benchmark_service.RESULTS_FILE).write_text(json.dumps([
        {"id": "rag-001", "accuracy": 0.5, "citation": 1.0, "recall": 1.0,
         "missing_facts": ["semantic vector retrieval"], "answer": "..."},
        {"id": "rag-002", "accuracy": 1.0, "citation": 1.0, "recall": 1.0},
    ]))
    champ = Champion(version="9.9.9", sut_path=str(tmp_path / "sut"))
    misses = benchmark_service.champion_misses(champ)
    assert [m["id"] for m in misses] == ["rag-001"]
    assert misses[0]["question"] == "What is hybrid retrieval?"
    assert misses[0]["missing_facts"] == ["semantic vector retrieval"]
