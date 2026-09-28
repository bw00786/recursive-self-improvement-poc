"""Security boundary for candidate modifications.

The improvement agent may ONLY touch files inside its own candidate workspace,
and only whitelisted relative paths. The benchmark, evaluator, promotion rules,
and this file are outside its reach by construction.
"""
from __future__ import annotations

import re
from pathlib import Path

# Files a candidate is allowed to create/modify, relative to candidate root.
ALLOWED_CANDIDATE_FILES = {
    "sut/pipeline.yaml",
    "sut/retrieval.py",
    "sut/rerank.py",
    "sut/rewrite.py",
}

# pipeline.yaml keys a candidate may change.
ALLOWED_CONFIG_KEYS = {
    "system_prompt",
    "query_rewrite",
    "retrieval",
    "rerank",
    "top_k",
    "temperature",
    "max_context_chars",
}
ALLOWED_RETRIEVAL_MODES = {"none", "keyword", "vector", "hybrid"}

# Crude but effective static screen for candidate-authored code.
FORBIDDEN_CODE_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bsubprocess\b",
        r"\bos\.system\b",
        r"\bsocket\b",
        r"\brequests\b",
        r"\bhttpx\b",
        r"\burllib\b",
        r"\bshutil\.rmtree\b",
        r"__import__",
        r"\beval\s*\(",
        r"\bexec\s*\(",
        r"open\s*\(\s*[\"']/(?!/)",  # absolute host paths
        r"\.\./",
    ]
]

FORBIDDEN_TARGET_DIRS = {"benchmark", ".git", ".env", "experiments/champion"}


class SecurityViolation(Exception):
    pass


def validate_relative_path(rel: str) -> str:
    rel = rel.replace("\\", "/").lstrip("/")
    if not rel or rel.startswith("..") or "/../" in f"/{rel}/" or re.match(r"^[a-zA-Z]:", rel):
        raise SecurityViolation(f"illegal path: {rel!r}")
    first = rel.split("/", 1)[0]
    if first in {d.split("/", 1)[0] for d in FORBIDDEN_TARGET_DIRS}:
        raise SecurityViolation(f"path targets forbidden area: {rel!r}")
    if rel not in ALLOWED_CANDIDATE_FILES:
        raise SecurityViolation(f"path not in candidate whitelist: {rel!r}")
    return rel


def resolve_within(base: Path, rel: str) -> Path:
    """Resolve rel inside base; reject symlinks/traversal escaping base."""
    rel = validate_relative_path(rel)
    target = (base / rel).resolve()
    base_resolved = base.resolve()
    if base_resolved != target and base_resolved not in target.parents:
        raise SecurityViolation(f"path escapes candidate workspace: {rel!r}")
    return target


def scan_code(content: str, rel: str) -> None:
    for pat in FORBIDDEN_CODE_PATTERNS:
        if pat.search(content):
            raise SecurityViolation(f"forbidden pattern {pat.pattern!r} in {rel}")


def validate_config_update(updates: dict) -> dict:
    clean: dict = {}
    for key, value in updates.items():
        if key not in ALLOWED_CONFIG_KEYS:
            raise SecurityViolation(f"config key not allowed: {key!r}")
        if key == "retrieval" and value not in ALLOWED_RETRIEVAL_MODES:
            raise SecurityViolation(f"illegal retrieval mode: {value!r}")
        if key in ("query_rewrite", "rerank") and not isinstance(value, bool):
            raise SecurityViolation(f"{key} must be boolean")
        if key == "top_k" and not (isinstance(value, int) and 1 <= value <= 20):
            raise SecurityViolation("top_k must be an int in [1, 20]")
        if key == "temperature" and not (isinstance(value, (int, float)) and 0.0 <= float(value) <= 1.0):
            raise SecurityViolation("temperature must be in [0, 1]")
        if key == "max_context_chars" and not (isinstance(value, int) and 200 <= value <= 32000):
            raise SecurityViolation("max_context_chars must be an int in [200, 32000]")
        if key == "system_prompt" and (not isinstance(value, str) or len(value) > 8000):
            raise SecurityViolation("system_prompt must be a string <= 8000 chars")
        clean[key] = value
    return clean
