"""Candidate execution sandbox.

Primary mode: Docker with CPU/memory limits, read-only mounts, and a timeout.
Fallback mode (local): a plain subprocess with a timeout — used only when Docker
is unavailable, and flagged in the result as non-isolated.

The benchmark + evaluator are mounted read-only; the candidate can never
modify them.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from ..config import get_settings


@dataclass
class SandboxResult:
    ok: bool
    metrics: dict | None = None
    items: list = field(default_factory=list)
    exit_code: int | None = None
    logs: str = ""
    isolated: bool = True
    error: str | None = None


def docker_available() -> bool:
    if not shutil.which("docker"):
        return False
    try:
        return subprocess.run(
            ["docker", "info"], capture_output=True, timeout=15
        ).returncode == 0
    except Exception:
        return False


def _parse_result(stdout: str) -> dict | None:
    stdout = stdout.strip()
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        # Find the last JSON object in noisy output.
        start = stdout.rfind('\n{')
        if start >= 0:
            try:
                return json.loads(stdout[start + 1:])
            except json.JSONDecodeError:
                return None
    return None


def run_candidate_benchmark(candidate_ws: Path) -> SandboxResult:
    settings = get_settings()
    mode = settings.sandbox_mode.lower()
    use_docker = mode == "docker" or (mode == "auto" and docker_available())
    if use_docker:
        return _run_docker(candidate_ws, settings)
    if mode == "docker":
        return SandboxResult(ok=False, error="docker unavailable", isolated=False)
    return _run_local(candidate_ws, settings)


def _env() -> dict[str, str]:
    s = get_settings()
    return {
        "OLLAMA_BASE_URL": s.ollama_base_url,
        "OLLAMA_MODEL": s.ollama_model,
        "MOCK_LLM": s.mock_llm,
        "SUT_LLM": s.mock_llm,
    }


def _run_docker(ws: Path, settings) -> SandboxResult:
    env = _env()
    # Inside the container, Ollama on the host is reached via host.docker.internal.
    if "localhost" in env["OLLAMA_BASE_URL"] or "127.0.0.1" in env["OLLAMA_BASE_URL"]:
        env["OLLAMA_BASE_URL"] = env["OLLAMA_BASE_URL"].replace(
            "localhost", "host.docker.internal").replace("127.0.0.1", "host.docker.internal")
    cmd = [
        "docker", "run", "--rm",
        "--cpus", str(settings.sandbox_cpu_limit),
        "--memory", str(settings.sandbox_memory_limit),
        "--add-host", "host.docker.internal:host-gateway",
        "-v", f"{ws.resolve()}:/work:ro",
        "-v", f"{settings.benchmark_dir.resolve()}:/benchmark:ro",
    ]
    for k, v in env.items():
        cmd += ["-e", f"{k}={v}"]
    cmd += [
        settings.sandbox_image,
        "python", "/benchmark/evaluator.py",
        "--sut", "/work/sut",
        "--benchmark", "/benchmark/benchmark.json",
        "--out", "-",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=settings.sandbox_timeout_seconds)
    except subprocess.TimeoutExpired:
        return SandboxResult(ok=False, error="sandbox timeout", isolated=True)
    result = _parse_result(proc.stdout)
    if proc.returncode != 0 or not result:
        return SandboxResult(ok=False, exit_code=proc.returncode,
                             logs=(proc.stdout + proc.stderr)[-4000:],
                             error="candidate execution failed")
    return SandboxResult(ok=True, metrics=result["metrics"], items=result["items"],
                         exit_code=0, logs=proc.stderr[-2000:])


def _run_local(ws: Path, settings) -> SandboxResult:
    """Non-isolated fallback: subprocess with timeout, structured argv (no shell)."""
    import os
    env = {**os.environ, **_env()}
    cmd = [
        sys.executable, str(settings.benchmark_dir / "evaluator.py"),
        "--sut", str(ws / "sut"),
        "--benchmark", str(settings.benchmark_dir / "benchmark.json"),
        "--out", "-",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=settings.sandbox_timeout_seconds, env=env)
    except subprocess.TimeoutExpired:
        return SandboxResult(ok=False, error="sandbox timeout", isolated=False)
    result = _parse_result(proc.stdout)
    if proc.returncode != 0 or not result:
        return SandboxResult(ok=False, exit_code=proc.returncode, isolated=False,
                             logs=(proc.stdout + proc.stderr)[-4000:],
                             error="candidate execution failed")
    return SandboxResult(ok=True, metrics=result["metrics"], items=result["items"],
                         exit_code=0, logs=proc.stderr[-2000:], isolated=False)
