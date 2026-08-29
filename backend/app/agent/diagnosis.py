"""Deterministic diagnosis rules. No LLM."""

from __future__ import annotations

from app.agent.schemas import DetectedEvent, DiagnosisResult

TEMPORARY_REASONS = {"network_error", "processor_timeout", "session_timeout"}
FUNDS_REASONS = {"insufficient_funds"}
EXPIRED_REASONS = {"card_expired"}
DECLINED_REASONS = {"card_declined"}
FRAUD_REASONS = {"fraud_hold"}
CLOSED_REASONS = {"account_closed", "plan_cancelled_intent"}


def diagnose(event: DetectedEvent) -> DiagnosisResult:
    """Explain why revenue is at risk and how recoverable it looks."""
    reason = event.failure_reason
    event_type = event.event_type

    if event_type == "checkout_abandonment":
        intent = "high" if event.checkout_visits >= 3 else "uncertain"
        recoverability = "recoverable" if event.checkout_visits >= 3 else "potentially_recoverable"
        if reason in {"shipping_cost", "comparison_shopping"}:
            recoverability = "potentially_recoverable"
            intent = "price_sensitive"
        return DiagnosisResult(
            diagnosis_code="checkout_abandonment",
            diagnosis_text=(
                "Customer reached checkout but did not complete payment. "
                f"Purchase intent looks {intent} based on checkout visits "
                f"({event.checkout_visits}) and reason '{reason}'."
            ),
            recoverability=recoverability,
            recommended_direction="send_checkout_reminder",
        )

    if reason in TEMPORARY_REASONS:
        return DiagnosisResult(
            diagnosis_code="temporary_payment_issue",
            diagnosis_text=(
                "Temporary bank or network failure. The payment issue looks "
                "transient and delayed retry is appropriate."
            ),
            recoverability="recoverable",
            recommended_direction="retry_later",
        )

    if reason in FUNDS_REASONS:
        return DiagnosisResult(
            diagnosis_code="insufficient_funds",
            diagnosis_text=(
                "Customer or payment-method issue: insufficient funds. "
                "Recovery may require a delayed retry or an alternate payment method."
            ),
            recoverability="potentially_recoverable",
            recommended_direction="retry_later",
        )

    if reason in EXPIRED_REASONS:
        direction = (
            "send_subscription_update_request"
            if event_type == "subscription_failure"
            else "request_alternate_payment"
        )
        return DiagnosisResult(
            diagnosis_code="expired_card",
            diagnosis_text=(
                "Payment method problem: the card is expired. "
                "Request an updated or alternate payment method."
            ),
            recoverability="recoverable",
            recommended_direction=direction,
        )

    if reason in DECLINED_REASONS:
        return DiagnosisResult(
            diagnosis_code="card_declined",
            diagnosis_text=(
                "The card was declined. This may recover with a later retry, "
                "or it may need an alternate payment method after repeated failures."
            ),
            recoverability="potentially_recoverable",
            recommended_direction="retry_later",
        )

    if reason in FRAUD_REASONS:
        return DiagnosisResult(
            diagnosis_code="fraud_hold",
            diagnosis_text=(
                "The payment was held for suspected fraud. Automated recovery "
                "is risky; manual review is appropriate."
            ),
            recoverability="unlikely",
            recommended_direction="escalate_to_manual_review",
        )

    if reason in CLOSED_REASONS:
        return DiagnosisResult(
            diagnosis_code="account_or_plan_closed",
            diagnosis_text=(
                "The account looks closed or the customer intends to cancel. "
                "Automated recovery is unlikely."
            ),
            recoverability="unlikely",
            recommended_direction="escalate_to_manual_review",
        )

    if event_type == "subscription_failure":
        return DiagnosisResult(
            diagnosis_code="subscription_failure",
            diagnosis_text=(
                "Recurring payment issue. Evaluate customer history and payment "
                f"method ({event.payment_method}) before requesting an update or retrying."
            ),
            recoverability="potentially_recoverable",
            recommended_direction="send_subscription_update_request",
        )

    return DiagnosisResult(
        diagnosis_code="payment_failure",
        diagnosis_text=(
            f"Payment failed with reason '{reason}'. Recoverability depends on "
            "history, retry count, and payment method."
        ),
        recoverability="potentially_recoverable",
        recommended_direction="retry_later",
    )
