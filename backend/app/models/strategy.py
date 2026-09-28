from __future__ import annotations

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class StrategyStat(Base):
    """Learned experiment-selection statistics — the recursive layer's memory."""

    __tablename__ = "strategies"

    strategy: Mapped[str] = mapped_column(String(128), primary_key=True)
    experiment_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[float] = mapped_column(Float, default=0.0)
    average_improvement: Mapped[float] = mapped_column(Float, default=0.0)
