from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import ChampionOut
from ..services import benchmark_service

router = APIRouter(tags=["benchmark"])


@router.post("/api/benchmark/run", response_model=ChampionOut)
def run_baseline(db: Session = Depends(get_db)):
    """(Re-)run the immutable benchmark against the active champion."""
    return benchmark_service.run_baseline(db)
