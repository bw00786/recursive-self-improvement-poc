"""Run one improvement cycle end-to-end (no API server needed).

    python scripts/run_experiment.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.database import SessionLocal, init_db  # noqa: E402
from backend.app.graph.improvement_graph import run_experiment_sync  # noqa: E402
from backend.app.models import Experiment  # noqa: E402


def main() -> None:
    init_db()
    with SessionLocal() as db:
        exp = Experiment(objective="Improve the benchmark score")
        db.add(exp)
        db.commit()
        exp_id = exp.id
    print(f"experiment {exp_id} running...")
    result = run_experiment_sync(exp_id)
    with SessionLocal() as db:
        exp = db.get(Experiment, exp_id)
        print(f"status:   {exp.status}")
        print(f"strategy: {exp.strategy}")
        print(f"score:    {exp.result_score}")
        if exp.error:
            print(f"error:    {exp.error}")
    print(f"decision: {result.get('decision')}")


if __name__ == "__main__":
    main()
