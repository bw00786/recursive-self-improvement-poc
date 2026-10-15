from backend.app.models import Champion
from backend.app.services import promotion_service


def _champion(score=80.0, accuracy=0.8, citation=0.8):
    return Champion(version="0.1.0", sut_path="/tmp/x", score=score, metrics={
        "accuracy": accuracy, "citation_accuracy": citation,
        "overall_score": score, "latency_avg_s": 1.0, "failure_rate": 0.0,
    })


def test_improvement_passes_gate():
    d = promotion_service.compare(
        {"overall_score": 84.7, "accuracy": 0.85, "citation_accuracy": 0.9,
         "latency_avg_s": 1.2, "failure_rate": 0.0}, _champion())
    assert d["passed"] and d["delta"] == 4.7


def test_regression_rejected():
    d = promotion_service.compare(
        {"overall_score": 84.7, "accuracy": 0.70, "citation_accuracy": 0.9,
         "latency_avg_s": 1.2, "failure_rate": 0.0}, _champion())
    assert not d["passed"]
    assert any("accuracy regressed" in v for v in d["hard_violations"])


def test_small_regression_within_tolerance_passes(monkeypatch):
    from backend.app.config import get_settings
    monkeypatch.setattr(get_settings(), "non_regression_tolerance", 0.01)
    metrics = {"overall_score": 84.7, "accuracy": 0.795, "citation_accuracy": 0.9,
               "latency_avg_s": 1.2, "failure_rate": 0.0}
    assert promotion_service.compare(metrics, _champion())["passed"]
    metrics["accuracy"] = 0.785
    assert not promotion_service.compare(metrics, _champion())["passed"]


def test_insufficient_improvement_rejected():
    d = promotion_service.compare(
        {"overall_score": 80.2, "accuracy": 0.8, "citation_accuracy": 0.8,
         "latency_avg_s": 1.0, "failure_rate": 0.0}, _champion())
    assert not d["passed"]


def test_latency_noise_excluded_from_delta():
    champ = _champion(score=97.16)
    champ.metrics["latency_score"] = 0.94
    # Same quality, faster run: +0.5 overall comes only from latency -> rejected.
    d = promotion_service.compare(
        {"overall_score": 97.66, "accuracy": 0.8, "citation_accuracy": 0.8,
         "latency_score": 1.0, "latency_avg_s": 1.0, "failure_rate": 0.0}, champ)
    assert not d["passed"] and d["quality_delta"] < 0.5
    # Better quality, slower run: overall +0.2 but quality +0.7 -> passes.
    d = promotion_service.compare(
        {"overall_score": 97.36, "accuracy": 0.82, "citation_accuracy": 0.8,
         "latency_score": 0.84, "latency_avg_s": 2.4, "failure_rate": 0.0}, champ)
    assert d["passed"] and d["quality_delta"] == 0.7


def test_latency_hard_limit():
    d = promotion_service.compare(
        {"overall_score": 99.0, "accuracy": 0.99, "citation_accuracy": 0.99,
         "latency_avg_s": 999.0, "failure_rate": 0.0}, _champion())
    assert not d["passed"]
    assert any("latency" in v for v in d["hard_violations"])


def test_failures_hard_reject():
    d = promotion_service.compare(
        {"overall_score": 99.0, "accuracy": 0.99, "citation_accuracy": 0.99,
         "latency_avg_s": 1.0, "failure_rate": 0.05}, _champion())
    assert not d["passed"]


def test_stale_candidate_cannot_be_promoted():
    import pytest
    from backend.app.database import SessionLocal
    from backend.app.models import Candidate
    from backend.app.services import benchmark_service

    with SessionLocal() as db:
        active = benchmark_service.ensure_champion(db)
        stale = Candidate(parent_version="0.0.1", status="AWAITING_APPROVAL",
                          metrics={"overall_score": 99.0})
        with pytest.raises(RuntimeError, match=f"champion is now v{active.version}"):
            promotion_service.promote(db, stale, approved_by="test")
        assert db.query(Champion).filter_by(status="active").one().version == active.version
