"""Deterministic strategy selection. No LLM."""

from __future__ import annotations

from app.agent.schemas import DetectedEvent, DiagnosisResult, ScoreResult, StrategyResult

LOW_PROBABILITY = 0.22
HIGH_PROBABILITY = 0.60


def choose_strategy(
    event: DetectedEvent,
    diagnosis: DiagnosisResult,
    score: ScoreResult,
) -> StrategyResult:
    """Select a recovery strategy from event type, diagnosis, score, and retries."""
    probability = score.probability
    reason = event.failure_reason
    retries = event.retry_count

    if diagnosis.diagnosis_code in {"fraud_hold", "account_or_plan_closed"}:
        return StrategyResult(
            strategy="escalate_to_manual_review",
            reason="Hard failure (fraud hold or closed account/plan) is not safe for automated recovery.",
        )

    if probability < LOW_PROBABILITY:
        if retries >= 3 or diagnosis.recoverability == "unlikely":
            return StrategyResult(
                strategy="escalate_to_manual_review",
                reason="Recovery probability is low after repeated or unlikely failures.",
            )
        return StrategyResult(
            strategy="do_nothing",
            reason="Recovery probability is too low to justify an automated action.",
        )

    if diagnosis.diagnosis_code == "expired_card":
        if event.event_type == "subscription_failure":
            return StrategyResult(
                strategy="send_subscription_update_request",
                reason="Expired card on a subscription requires an updated payment method.",
            )
        return StrategyResult(
            strategy="request_alternate_payment",
            reason="Expired card requires an alternate or updated payment method.",
        )

    if event.event_type == "checkout_abandonment":
        high_intent = event.checkout_visits >= 3 or probability >= HIGH_PROBABILITY
        if high_intent:
            return StrategyResult(
                strategy="send_checkout_reminder",
                reason="Checkout abandonment with meaningful purchase intent.",
            )
        if probability < 0.30:
            return StrategyResult(
                strategy="do_nothing",
                reason="Checkout abandonment with low intent and modest recovery probability.",
            )
        return StrategyResult(
            strategy="send_checkout_reminder",
            reason="Checkout abandonment is still worth a reminder.",
        )

    if event.event_type == "subscription_failure":
        if retries >= 3 or reason == "dunning_unresponsive":
            if probability >= 0.40:
                return StrategyResult(
                    strategy="send_subscription_update_request",
                    reason="Repeated subscription failure; ask the customer to update payment details.",
                )
            return StrategyResult(
                strategy="escalate_to_manual_review",
                reason="Repeated subscription failure with weak recovery odds.",
            )
        if diagnosis.diagnosis_code == "temporary_payment_issue":
            return StrategyResult(
                strategy="retry_later",
                reason="Temporary subscription payment issue; delay and retry.",
            )
        if diagnosis.diagnosis_code == "insufficient_funds":
            return StrategyResult(
                strategy="retry_later",
                reason="Insufficient funds on a subscription; retry later in the billing cycle.",
            )
        return StrategyResult(
            strategy="send_subscription_update_request",
            reason="Recurring payment failed; request a payment-method update.",
        )

    # payment_failure
    if diagnosis.diagnosis_code == "temporary_payment_issue":
        if probability >= HIGH_PROBABILITY and retries == 0:
            return StrategyResult(
                strategy="retry_later",
                reason="Temporary failure with high recovery probability; delayed retry is appropriate.",
            )
        if retries >= 2:
            return StrategyResult(
                strategy="retry_later" if probability >= 0.45 else "request_alternate_payment",
                reason="Temporary failure already retried; delay again or request another method.",
            )
        return StrategyResult(
            strategy="retry_later",
            reason="Temporary bank/network failure; delayed retry is appropriate.",
        )

    if diagnosis.diagnosis_code == "insufficient_funds":
        if retries >= 3:
            return StrategyResult(
                strategy="request_alternate_payment",
                reason="Insufficient funds after several retries; request another payment method.",
            )
        return StrategyResult(
            strategy="retry_later",
            reason="Insufficient funds; retry later rather than immediately.",
        )

    if diagnosis.diagnosis_code == "card_declined" and retries >= 2:
        return StrategyResult(
            strategy="request_alternate_payment",
            reason="Card declined repeatedly; request an alternate payment method.",
        )

    if retries == 0 and probability >= HIGH_PROBABILITY:
        return StrategyResult(
            strategy="retry_now",
            reason="First attempt with high recovery probability can be retried immediately.",
        )

    return StrategyResult(
        strategy="retry_later",
        reason="Standard payment failure; schedule a later retry.",
    )
