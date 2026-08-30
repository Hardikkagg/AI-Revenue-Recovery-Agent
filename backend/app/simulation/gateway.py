"""Simulated Payment Gateway for safe, sandbox recovery execution."""

from __future__ import annotations

import hashlib
import random
import uuid

from app.simulation.schemas import SimulatedGatewayResult

# High-recoverability vs hard-failure codes
RECOVERABLE_CODES = {
    "network_error",
    "processor_timeout",
    "gateway_unavailable",
    "system_error",
    "temporary_payment_issue",
}

UNRECOVERABLE_CODES = {
    "fraud_hold",
    "fraud_suspected",
    "account_closed",
    "account_or_plan_closed",
    "card_reported_lost",
    "stolen_card",
    "do_not_honor",
}


class SimulatedPaymentGateway:
    """Sandbox Payment Gateway. Never makes external HTTP calls or processes real cards."""

    def __init__(self, seed: int | None = None) -> None:
        self._seed = seed

    def _get_rng(self, customer_id: int, event_id: int | None = None) -> random.Random:
        """Create a reproducible Random instance based on customer/event seed using stable SHA-256."""
        if self._seed is not None:
            return random.Random(self._seed)
        seed_raw = f"{customer_id}:{event_id or 0}:gateway".encode("utf-8")
        seed_val = int(hashlib.sha256(seed_raw).hexdigest()[:16], 16)
        return random.Random(seed_val)


    def execute_retry(
        self,
        customer_id: int,
        amount: float,
        failure_reason: str,
        diagnosis_code: str,
        recovery_probability: float,
        retry_count: int = 0,
        is_delayed: bool = False,
        event_id: int | None = None,
    ) -> SimulatedGatewayResult:
        """Simulate a retry authorization against the sandbox payment processor."""
        reference = f"SIM-GW-{uuid.uuid4().hex[:8].upper()}"

        # Hard failure checks: Never recover fraud or closed accounts
        if (
            failure_reason in UNRECOVERABLE_CODES
            or diagnosis_code in UNRECOVERABLE_CODES
        ):
            return SimulatedGatewayResult(
                action_type="retry_delayed" if is_delayed else "retry_immediate",
                success=False,
                gateway_reference=reference,
                response_code="DECLINED_HARD_FAILURE",
                response_message=f"Simulated decline: {failure_reason} is a non-retryable terminal status.",
                amount_attempted=amount,
                amount_settled=0.0,
            )

        # Baseline effective probability computed from ML score and contextual modifiers
        # Delayed retries allow processor recovery or customer balance replenishment
        boost = 0.08 if is_delayed else 0.0
        if diagnosis_code in RECOVERABLE_CODES or failure_reason in RECOVERABLE_CODES:
            boost += 0.10

        # Excessive retries experience diminishing returns
        retry_penalty = min(0.30, retry_count * 0.08)

        effective_prob = max(0.05, min(0.95, recovery_probability + boost - retry_penalty))

        rng = self._get_rng(customer_id, event_id)
        roll = rng.random()

        is_success = roll < effective_prob

        if is_success:
            return SimulatedGatewayResult(
                action_type="retry_delayed" if is_delayed else "retry_immediate",
                success=True,
                gateway_reference=reference,
                response_code="AUTH_200_SUCCESS",
                response_message=f"Simulated authorization approved for ${amount:.2f} (roll: {roll:.2f} < threshold: {effective_prob:.2f}).",
                amount_attempted=amount,
                amount_settled=amount,
            )

        return SimulatedGatewayResult(
            action_type="retry_delayed" if is_delayed else "retry_immediate",
            success=False,
            gateway_reference=reference,
            response_code="DECLINED_SOFT_FAILURE",
            response_message=f"Simulated retry declined by issuing bank (roll: {roll:.2f} >= threshold: {effective_prob:.2f}).",
            amount_attempted=amount,
            amount_settled=0.0,
        )
