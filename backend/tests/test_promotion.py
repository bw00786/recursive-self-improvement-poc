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


def test_insufficient_improvement_rejected():
    d = promotion_service.compare(
        {"overall_score": 80.2, "accuracy": 0.8, "citation_accuracy": 0.8,
         "latency_avg_s": 1.0, "failure_rate": 0.0}, _champion())
    assert not d["passed"]


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
