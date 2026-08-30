"""Pydantic schemas for learning, recovery metrics, and model adaptation."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class LearningFeedback(BaseModel):
    """One validated outcome observation for adaptive learning."""

    simulation_id: str = Field(..., min_length=1)
    customer_id: int | None = None
    event_id: int | None = None
    strategy: str = Field(..., min_length=1)
    amount_at_risk: float = Field(ge=0.0)
    recovered: bool = False
    recovered_amount: float = Field(ge=0.0)
    reward: float = Field(ge=-1.0, le=1.0)
    outcome: str = Field(..., min_length=1)


class StrategyPerformance(BaseModel):
    """Aggregated performance metrics for an individual recovery strategy."""

    strategy: str
    total_cases: int
    successful_recoveries: int
    failed_cases: int
    recovery_rate: float
    revenue_at_risk: float
    revenue_recovered: float


class RecoveryMetricsResponse(BaseModel):
    """Complete aggregated metrics for the recovery dashboard and learning system."""

    total_cases: int
    resolved_cases: int
    escalated_cases: int
    closed_cases: int
    overall_recovery_rate: float
    total_revenue_at_risk: float
    total_revenue_recovered: float
    strategy_breakdown: list[StrategyPerformance]
    feedback_samples_count: int


class RetrainResponse(BaseModel):
    """Response returned after executing a feedback-augmented model retrain."""

    success: bool
    promoted: bool = False
    message: str
    baseline_samples: int
    live_feedback_samples: int
    rejected_feedback_samples: int = 0
    total_training_samples: int
    holdout_metrics: dict[str, Any]
    cross_validation_5fold: dict[str, Any]
    current_holdout_metrics: dict[str, Any] = Field(default_factory=dict)
