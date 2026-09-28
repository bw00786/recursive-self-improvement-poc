from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Champion
from ..schemas import ChampionOut

router = APIRouter(tags=["champions"])


@router.get("/api/champion", response_model=ChampionOut)
def active_champion(db: Session = Depends(get_db)):
    champion = db.query(Champion).filter_by(status="active").first()
    if not champion:
        raise HTTPException(404, "no active champion — run POST /api/benchmark/run")
    return champion


@router.get("/api/champions", response_model=list[ChampionOut])
def champion_history(db: Session = Depends(get_db)):
    return db.query(Champion).order_by(Champion.created_at.asc()).all()
