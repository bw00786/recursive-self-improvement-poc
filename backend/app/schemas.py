"""Pydantic request/response models for the REST API."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ExperimentCreate(BaseModel):
    objective: str = "Improve the benchmark score"


class ExperimentOut(BaseModel):
    id: str
    objective: str
    parent_version: str
    hypothesis: dict | None
    strategy: str | None
    status: str
    error: str | None
    result_score: float | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class CandidateOut(BaseModel):
    id: str
    experiment_id: str
    parent_version: str
    description: str
    files_changed: list
    metrics: dict | None
    decision: dict | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChampionOut(BaseModel):
    id: int
    version: str
    score: float
    metrics: dict
    status: str
    created_at: datetime
    approved_by: str

    model_config = {"from_attributes": True}


class EvaluationOut(BaseModel):
    id: int
    candidate_id: str
    metric_name: str
    metric_value: float
    baseline_value: float | None
    delta: float | None
    passed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class StrategyOut(BaseModel):
    strategy: str
    experiment_count: int
    success_count: int
    success_rate: float
    average_improvement: float

    model_config = {"from_attributes": True}


class ApprovalRequest(BaseModel):
    approved_by: str = "human"
    reason: str = ""


class McpCallRequest(BaseModel):
    name: str
    arguments: dict = {}
