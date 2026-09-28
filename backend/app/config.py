"""Central configuration. Everything environment-specific lives here."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(REPO_ROOT / ".env"), extra="ignore")

    app_env: str = "development"

    # SQLite fallback keeps the demo runnable without Postgres.
    database_url: str = f"sqlite:///{REPO_ROOT / 'rail.db'}"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    mock_llm: str = "auto"  # auto | true | false

    langfuse_enabled: bool = False
    langfuse_host: str = ""
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    otel_enabled: bool = True

    sandbox_mode: str = "auto"  # auto | docker | local
    sandbox_image: str = "rail-sandbox:latest"
    sandbox_cpu_limit: str = "2"
    sandbox_memory_limit: str = "4g"
    sandbox_timeout_seconds: int = 300

    require_human_approval: bool = True
    hard_max_latency_seconds: float = 30.0
    min_score_improvement: float = 0.5
    eval_weights_json: str = ""

    repo_root: Path = REPO_ROOT

    @property
    def experiments_dir(self) -> Path:
        return self.repo_root / "experiments"

    @property
    def champion_dir(self) -> Path:
        return self.experiments_dir / "champion"

    @property
    def candidates_dir(self) -> Path:
        return self.experiments_dir / "candidates"

    @property
    def benchmark_dir(self) -> Path:
        return self.repo_root / "benchmark"

    @property
    def sut_source_dir(self) -> Path:
        return self.repo_root / "sut"

    @property
    def eval_weights(self) -> dict[str, float]:
        if self.eval_weights_json:
            try:
                return {k: float(v) for k, v in json.loads(self.eval_weights_json).items()}
            except Exception:
                pass
        return {
            "accuracy": 0.40,
            "citation_accuracy": 0.25,
            "retrieval_recall": 0.20,
            "reliability": 0.10,
            "latency_score": 0.05,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
