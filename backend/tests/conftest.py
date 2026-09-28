"""Test configuration: offline mock LLM, local (non-docker) sandbox, temp DB."""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("DATABASE_URL", f"sqlite:///{REPO_ROOT / 'test_rail.db'}")
os.environ.setdefault("MOCK_LLM", "true")
os.environ.setdefault("SANDBOX_MODE", "local")
os.environ.setdefault("SANDBOX_TIMEOUT_SECONDS", "240")

import pytest  # noqa: E402

# Fresh DB per test session so the promotion assertions are deterministic.
_db_file = REPO_ROOT / "test_rail.db"
if _db_file.exists():
    _db_file.unlink()


@pytest.fixture(scope="session", autouse=True)
def _init_db():
    from backend.app.database import init_db
    init_db()
    yield
