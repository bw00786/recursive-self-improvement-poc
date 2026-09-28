"""Bootstrap: create champion v0.1.0 and run the baseline benchmark.

    python scripts/bootstrap.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.database import SessionLocal, init_db  # noqa: E402
from backend.app.services import benchmark_service  # noqa: E402


def main() -> None:
    init_db()
    with SessionLocal() as db:
        champion = benchmark_service.run_baseline(db)
        print(f"Champion v{champion.version} baseline score: {champion.score:.2f}")
        for k, v in champion.metrics.items():
            print(f"  {k:20s} {v}")


if __name__ == "__main__":
    main()
