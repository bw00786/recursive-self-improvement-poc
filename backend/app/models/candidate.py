from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: f"cand-{uuid.uuid4().hex[:8]}")
    experiment_id: Mapped[str] = mapped_column(ForeignKey("experiments.id"), index=True)
    parent_version: Mapped[str] = mapped_column(String(32), default="")
    path: Mapped[str] = mapped_column(Text, default="")
    git_branch: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    files_changed: Mapped[list] = mapped_column(JSON, default=list)
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    decision: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="CREATED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
