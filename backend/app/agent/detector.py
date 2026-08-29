"""Event detection and normalization."""

from __future__ import annotations

from app.agent.schemas import SUPPORTED_EVENT_TYPES, DetectedEvent, RecoveryEventInput


class UnsupportedEventTypeError(ValueError):
    """Raised when the incoming event type is not supported."""


class InvalidEventError(ValueError):
    """Raised when a supported event is missing required normalized data."""


def detect(event: RecoveryEventInput) -> DetectedEvent:
    """Validate and normalize an incoming recovery event."""
    event_type = (event.event_type or "").strip().lower()
    if event_type not in SUPPORTED_EVENT_TYPES:
        supported = ", ".join(SUPPORTED_EVENT_TYPES)
        raise UnsupportedEventTypeError(
            f"Unsupported event type '{event.event_type}'. Supported types: {supported}."
        )

    failure_reason = (event.failure_reason or "").strip().lower() or "unspecified"
    payment_method = (event.payment_method or "").strip().lower() or "unknown"
    cart_value = event.cart_value if event.cart_value is not None else (
        event.amount if event_type == "checkout_abandonment" else 0.0
    )

    if event_type == "checkout_abandonment" and event.checkout_visits < 0:
        raise InvalidEventError("checkout_visits cannot be negative")

    return DetectedEvent(
        customer_id=event.customer_id,
        event_id=event.event_id,
        event_type=event_type,
        amount=round(float(event.amount), 2),
        payment_method=payment_method,
        failure_reason=failure_reason,
        customer_age=event.customer_age,
        account_age=max(0, event.account_age),
        previous_successes=max(0, event.previous_successes),
        previous_failures=max(0, event.previous_failures),
        retry_count=max(0, event.retry_count),
        checkout_visits=max(0, event.checkout_visits),
        cart_value=round(float(cart_value), 2),
        subscription_age=max(0, event.subscription_age),
        timestamp=event.timestamp,
    )
