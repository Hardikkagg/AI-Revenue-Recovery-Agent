"""Schemas for simulated execution and outcome observation."""

from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

from app.agent.schemas import AnalysisResult, DetectedEvent

SimulationStatus = Literal["completed", "escalated", "skipped", "failed"]
OutcomeType = Literal[
    "payment_recovered",
    "payment_failed",
    "customer_updated_payment",
    "customer_unresponsive",
    "checkout_completed",
    "checkout_abandoned",
    "manual_review_required",
    "no_action_taken",
]


class SimulatedCommunicationResult(BaseModel):
    """Result of a simulated customer communication action."""

    channel: Literal["email", "sms", "in_app"] = "email"
    status: Literal["simulated_sent", "skipped"] = "simulated_sent"
    template_name: str
    message: str
    customer_responded: bool = False
    response_delay_seconds: int = 0


class SimulatedGatewayResult(BaseModel):
    """Result of a simulated payment gateway retry."""

    gateway_name: str = "SimulatedPaymentGateway"
    action_type: str
    success: bool
    gateway_reference: str
    response_code: str
    response_message: str
    amount_attempted: float
    amount_settled: float = 0.0


class SimulationResult(BaseModel):
    """Structured result of executing a recovery strategy in the simulator."""

    simulation_id: str
    strategy: str
    status: SimulationStatus
    outcome: OutcomeType
    recovered: bool
    recovered_amount: float = Field(ge=0.0)
    amount_at_risk: float = Field(ge=0.0)
    execution_time_seconds: float
    explanation: str
    action_details: dict[str, Any] = Field(default_factory=dict)
    gateway_result: SimulatedGatewayResult | None = None
    communication_result: SimulatedCommunicationResult | None = None


class RecoverySimulationResponse(BaseModel):
    """Full API response for POST /recovery/simulate."""

    analysis: AnalysisResult
    simulation: SimulationResult
