import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from ..audit import audit
from ..database import get_db
from ..graph.improvement_graph import run_experiment_sync
from ..models import Candidate, Experiment
from ..schemas import CandidateOut, ExperimentCreate, ExperimentOut

router = APIRouter(tags=["experiments"])


@router.get("/api/experiments", response_model=list[ExperimentOut])
def list_experiments(db: Session = Depends(get_db)):
    return db.query(Experiment).order_by(Experiment.created_at.desc()).all()


@router.post("/api/experiments", response_model=ExperimentOut, status_code=201)
def create_experiment(body: ExperimentCreate, db: Session = Depends(get_db)):
    exp = Experiment(objective=body.objective)
    db.add(exp)
    db.commit()
    audit(db, "EXPERIMENT_CREATED", experiment=exp.id, objective=body.objective)
    return exp


@router.get("/api/experiments/{experiment_id}", response_model=ExperimentOut)
def get_experiment(experiment_id: str, db: Session = Depends(get_db)):
    exp = db.get(Experiment, experiment_id)
    if not exp:
        raise HTTPException(404, "experiment not found")
    return exp


@router.get("/api/experiments/{experiment_id}/candidates", response_model=list[CandidateOut])
def experiment_candidates(experiment_id: str, db: Session = Depends(get_db)):
    return db.query(Candidate).filter_by(experiment_id=experiment_id).all()


@router.post("/api/experiments/{experiment_id}/run", response_model=ExperimentOut)
async def run_experiment(experiment_id: str, background: BackgroundTasks,
                         db: Session = Depends(get_db)):
    exp = db.get(Experiment, experiment_id)
    if not exp:
        raise HTTPException(404, "experiment not found")
    if exp.status in ("RUNNING", "GENERATING", "EVALUATING"):
        raise HTTPException(409, f"experiment already running ({exp.status})")
    exp.status = "RUNNING"
    db.commit()
    background.add_task(asyncio.to_thread, run_experiment_sync, experiment_id)
    return exp
