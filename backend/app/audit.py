"""Audit log — every important event is recorded."""
from __future__ import annotations

from sqlalchemy.orm import Session

from .models import AuditLog


def audit(db: Session, event: str, **details) -> None:
    db.add(AuditLog(event=event, details=details))
    db.commit()
