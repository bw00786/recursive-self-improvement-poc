"""Persist per-metric evaluation rows for a candidate."""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import Candidate, Champion, Evaluation


def store_evaluations(db: Session, candidate: Candidate, metrics: dict,
                      champion: Champion) -> list[Evaluation]:
    base = champion.metrics or {}
    rows: list[Evaluation] = []
    for name, value in metrics.items():
        if not isinstance(value, (int, float)):
            continue
        baseline = base.get(name)
        delta = (value - baseline) if isinstance(baseline, (int, float)) else None
        rows.append(Evaluation(
            candidate_id=candidate.id,
            metric_name=name,
            metric_value=float(value),
            baseline_value=float(baseline) if isinstance(baseline, (int, float)) else None,
            delta=round(delta, 4) if delta is not None else None,
            passed=(delta or 0.0) >= 0.0,
        ))
    db.add_all(rows)
    db.commit()
    return rows
