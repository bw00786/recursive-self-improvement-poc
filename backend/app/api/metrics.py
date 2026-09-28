from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Candidate, Champion, Experiment, StrategyStat
from ..schemas import StrategyOut

router = APIRouter(tags=["metrics"])


@router.get("/api/metrics")
def dashboard_metrics(db: Session = Depends(get_db)):
    exps = db.query(Experiment).all()
    champion = db.query(Champion).filter_by(status="active").first()
    promoted = [e for e in exps if e.status == "PROMOTED"]
    return {
        "champion": {
            "version": champion.version,
            "score": champion.score,
            "metrics": champion.metrics,
        } if champion else None,
        "experiments_total": len(exps),
        "experiments_promoted": len(promoted),
        "experiments_rejected": len([e for e in exps if e.status == "REJECTED"]),
        "experiments_failed": len([e for e in exps if e.status == "FAILED"]),
        "awaiting_approval": db.query(Candidate).filter_by(status="AWAITING_APPROVAL").count(),
        "running": [e.id for e in exps if e.status in ("RUNNING", "GENERATING", "EVALUATING")],
    }


@router.get("/api/strategies", response_model=list[StrategyOut])
def strategies(db: Session = Depends(get_db)):
    return (db.query(StrategyStat)
            .order_by(StrategyStat.success_rate.desc()).all())
