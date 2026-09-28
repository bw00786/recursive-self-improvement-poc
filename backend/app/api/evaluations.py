from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuditLog, Evaluation
from ..schemas import EvaluationOut

router = APIRouter(tags=["evaluations"])


@router.get("/api/evaluations/{candidate_id}", response_model=list[EvaluationOut])
def candidate_evaluations(candidate_id: str, db: Session = Depends(get_db)):
    return (db.query(Evaluation).filter_by(candidate_id=candidate_id)
            .order_by(Evaluation.id.asc()).all())


@router.get("/api/audit")
def audit_log(limit: int = 100, db: Session = Depends(get_db)):
    rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(min(limit, 500)).all()
    return [{"ts": r.ts.isoformat(), "event": r.event, "details": r.details} for r in rows]
