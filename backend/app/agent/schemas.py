"""Recovery event and analysis schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SUPPORTED_EVENT_TYPES = (
    "payment_failure",
    "checkout_abandonment",
    "subscription_failure",
)

STRATEGIES = (
    "retry_now",
    "retry_later",
    "request_alternate_payment",
    "send_checkout_reminder",
    "send_subscription_update_request",
    "escalate_to_manual_review",
    "do_nothing",
)

from app.llm.schemas import LLMGenerationResult

Confidence = Literal["LOW", "MEDIUM", "HIGH"]
Recoverability = Literal["recoverable", "potentially_recoverable", "unlikely"]


class RecoveryEventInput(BaseModel):
    """Incoming recovery event accepted by the agent and API."""

    customer_id: int
    event_type: str
    amount: float = Field(gt=0)
    event_id: int | None = None
    payment_method: str | None = None
    failure_reason: str | None = None
    customer_age: int | None = None
    account_age: int = 0
    previous_successes: int = 0
    previous_failures: int = 0
    retry_count: int = 0
    checkout_visits: int = 0
    cart_value: float | None = None
    subscription_age: int = 0
    timestamp: str | None = None


class DetectedEvent(BaseModel):
    """Normalized event after detection."""

    customer_id: int
    event_id: int | None
    event_type: str
    amount: float
    payment_method: str
    failure_reason: str
    customer_age: int | None
    account_age: int
    previous_successes: int
    previous_failures: int
    retry_count: int
    checkout_visits: int
    cart_value: float
    subscription_age: int
    timestamp: str | None


class DiagnosisResult(BaseModel):
    diagnosis_code: str
    diagnosis_text: str
    recoverability: Recoverability
    recommended_direction: str


class ScoreResult(BaseModel):
    probability: float = Field(ge=0, le=1)
    confidence: Confidence
    factors: list[str]


class StrategyResult(BaseModel):
    strategy: str
    reason: str


class AnalysisResult(BaseModel):
    event: DetectedEvent
    detected_event_type: str
    diagnosis: DiagnosisResult
    recovery_probability: float
    confidence: Confidence
    recommended_strategy: str
    reasoning: list[str]
    score_factors: list[str]
    strategy_reason: str
    llm_generation: LLMGenerationResult | None = None

