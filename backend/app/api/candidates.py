from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Candidate
from ..schemas import ApprovalRequest, CandidateOut
from ..services import promotion_service

router = APIRouter(tags=["candidates"])


@router.get("/api/candidates", response_model=list[CandidateOut])
def list_candidates(db: Session = Depends(get_db)):
    return db.query(Candidate).order_by(Candidate.created_at.desc()).all()


@router.get("/api/candidates/{candidate_id}", response_model=CandidateOut)
def get_candidate(candidate_id: str, db: Session = Depends(get_db)):
    cand = db.get(Candidate, candidate_id)
    if not cand:
        raise HTTPException(404, "candidate not found")
    return cand


@router.post("/api/candidates/{candidate_id}/approve")
def approve(candidate_id: str, body: ApprovalRequest, db: Session = Depends(get_db)):
    cand = db.get(Candidate, candidate_id)
    if not cand:
        raise HTTPException(404, "candidate not found")
    if cand.status != "AWAITING_APPROVAL":
        raise HTTPException(409, f"candidate is {cand.status}, not AWAITING_APPROVAL")
    champion = promotion_service.promote(db, cand, body.approved_by, body.reason)
    return {"promoted": True, "new_champion": champion.version, "score": champion.score}


@router.post("/api/candidates/{candidate_id}/reject")
def reject(candidate_id: str, body: ApprovalRequest, db: Session = Depends(get_db)):
    cand = db.get(Candidate, candidate_id)
    if not cand:
        raise HTTPException(404, "candidate not found")
    if cand.status != "AWAITING_APPROVAL":
        raise HTTPException(409, f"candidate is {cand.status}, not AWAITING_APPROVAL")
    promotion_service.reject(db, cand, body.approved_by, body.reason)
    return {"rejected": True}
