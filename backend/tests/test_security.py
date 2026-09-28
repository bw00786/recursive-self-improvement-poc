import pytest

from backend.app import security


def test_whitelisted_path_ok():
    assert security.validate_relative_path("sut/pipeline.yaml") == "sut/pipeline.yaml"


@pytest.mark.parametrize("bad", [
    "../benchmark/evaluator.py",
    "sut/../../benchmark/benchmark.json",
    "/etc/passwd",
    "C:/windows/system32",
    "benchmark/evaluator.py",
    "sut/evil.py",           # not whitelisted
    "experiments/champion/x",
    "",
])
def test_illegal_paths_rejected(bad):
    with pytest.raises(security.SecurityViolation):
        security.validate_relative_path(bad)


def test_forbidden_code_detected():
    with pytest.raises(security.SecurityViolation):
        security.scan_code("import subprocess\nsubprocess.run(['rm'])", "sut/retrieval.py")
    with pytest.raises(security.SecurityViolation):
        security.scan_code("eval('1+1')", "sut/retrieval.py")


def test_config_update_validation():
    clean = security.validate_config_update({"retrieval": "hybrid", "top_k": 6})
    assert clean == {"retrieval": "hybrid", "top_k": 6}
    with pytest.raises(security.SecurityViolation):
        security.validate_config_update({"retrieval": "everything"})
    with pytest.raises(security.SecurityViolation):
        security.validate_config_update({"evaluator_weights": {}})
    with pytest.raises(security.SecurityViolation):
        security.validate_config_update({"top_k": 999})
