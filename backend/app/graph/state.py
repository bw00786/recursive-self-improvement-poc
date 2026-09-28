from __future__ import annotations

from typing import Any, TypedDict


class ImprovementState(TypedDict, total=False):
    experiment_id: str
    objective: str

    champion_version: str
    champion_score: float
    current_metrics: dict[str, Any]

    analysis: dict[str, Any]
    failures: list
    hypothesis: dict[str, Any] | None
    research: list[str]

    candidate_id: str | None
    candidate_path: str | None
    candidate_metrics: dict[str, Any] | None

    comparison: dict[str, Any] | None
    decision: str | None
    approval_required: bool
    interpretation: str
