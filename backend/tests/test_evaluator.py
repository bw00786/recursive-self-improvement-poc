"""The mock LLM answers purely from retrieved context, so retrieval quality
must drive benchmark metrics: no retrieval < hybrid retrieval."""
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def _eval(sut_dir: Path) -> dict:
    from benchmark.evaluator import evaluate
    from sut.llm import MockLLM
    return evaluate(sut_dir, REPO_ROOT / "benchmark" / "benchmark.json", llm=MockLLM())


def test_baseline_without_retrieval_scores_low():
    result = _eval(REPO_ROOT / "sut")  # pipeline.yaml: retrieval=none
    m = result["metrics"]
    assert m["retrieval_recall"] == 0.0
    assert m["accuracy"] < 0.2
    assert m["reliability"] == 1.0


def test_hybrid_retrieval_scores_high(tmp_path):
    import shutil
    dest = tmp_path / "cand" / "sut"
    shutil.copytree(REPO_ROOT / "sut", dest)
    cfg = yaml.safe_load((dest / "pipeline.yaml").read_text())
    cfg["retrieval"] = "hybrid"
    (dest / "pipeline.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))
    m = _eval(dest)["metrics"]
    assert m["retrieval_recall"] > 0.8
    assert m["accuracy"] > 0.8
    assert m["citation_accuracy"] > 0.8
    assert m["overall_score"] > 85.0
