"""Tests for the recovery agent analysis pipeline."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.agent import RecoveryAgent
from app.agent.detector import UnsupportedEventTypeError, detect
from app.agent.schemas import RecoveryEventInput
from app.main import app

client = TestClient(app)
agent = RecoveryAgent()


def _event(**overrides) -> RecoveryEventInput:
    payload = {
        "customer_id": 1,
        "event_type": "payment_failure",
        "amount": 42.50,
        "payment_method": "card",
        "failure_reason": "network_error",
        "previous_successes": 4,
        "previous_failures": 0,
        "retry_count": 0,
        "checkout_visits": 0,
        "subscription_age": 0,
    }
    payload.update(overrides)
    return RecoveryEventInput(**payload)


def test_payment_failure_temporary() -> None:
    result = agent.analyze(_event(failure_reason="network_error", previous_successes=5))
    assert result.detected_event_type == "payment_failure"
    assert result.diagnosis.diagnosis_code == "temporary_payment_issue"
    assert result.diagnosis.recoverability == "recoverable"
    assert result.recovery_probability > 0.55
    assert result.recommended_strategy == "retry_later"
    assert result.confidence in {"LOW", "MEDIUM", "HIGH"}


def test_checkout_abandonment() -> None:
    result = agent.analyze(
        _event(
            event_type="checkout_abandonment",
            failure_reason="payment_form_dropoff",
            checkout_visits=5,
            cart_value=88.0,
            amount=88.0,
        )
    )
    assert result.detected_event_type == "checkout_abandonment"
    assert result.diagnosis.diagnosis_code == "checkout_abandonment"
    assert "checkout" in result.diagnosis.diagnosis_text.lower()
    assert result.recommended_strategy == "send_checkout_reminder"


def test_subscription_failure() -> None:
    result = agent.analyze(
        _event(
            event_type="subscription_failure",
            failure_reason="dunning_unresponsive",
            subscription_age=400,
            retry_count=1,
            previous_successes=3,
        )
    )
    assert result.detected_event_type == "subscription_failure"
    assert result.diagnosis.diagnosis_code == "subscription_failure"
    assert result.recommended_strategy in {
        "send_subscription_update_request",
        "escalate_to_manual_review",
        "retry_later",
    }


def test_expired_card() -> None:
    result = agent.analyze(_event(failure_reason="card_expired", event_type="payment_failure"))
    assert result.diagnosis.diagnosis_code == "expired_card"
    assert result.recommended_strategy == "request_alternate_payment"

    sub = agent.analyze(
        _event(
            event_type="subscription_failure",
            failure_reason="card_expired",
            subscription_age=200,
        )
    )
    assert sub.diagnosis.diagnosis_code == "expired_card"
    assert sub.recommended_strategy == "send_subscription_update_request"


def test_low_recovery_probability() -> None:
    result = agent.analyze(
        _event(
            failure_reason="fraud_hold",
            amount=400.0,
            previous_successes=0,
            previous_failures=8,
            retry_count=5,
        )
    )
    assert result.recovery_probability < 0.25
    assert result.recommended_strategy in {"do_nothing", "escalate_to_manual_review"}
    assert result.diagnosis.diagnosis_code == "fraud_hold"


def test_invalid_event_type_raises() -> None:
    with pytest.raises(UnsupportedEventTypeError, match="Unsupported event type"):
        detect(_event(event_type="chargeback_mystery"))


def test_analyze_endpoint() -> None:
    response = client.post(
        "/recovery/analyze",
        json={
            "customer_id": 9,
            "event_type": "payment_failure",
            "amount": 25.0,
            "payment_method": "card",
            "failure_reason": "network_error",
            "previous_successes": 6,
            "previous_failures": 0,
            "retry_count": 0,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["detected_event_type"] == "payment_failure"
    assert data["diagnosis"]["diagnosis_code"] == "temporary_payment_issue"
    assert data["recommended_strategy"] == "retry_later"
    assert 0 <= data["recovery_probability"] <= 1
    assert data["confidence"] in {"LOW", "MEDIUM", "HIGH"}
    assert "reasoning" in data and data["reasoning"]


def test_analyze_endpoint_rejects_invalid_event_type() -> None:
    response = client.post(
        "/recovery/analyze",
        json={"customer_id": 1, "event_type": "not_a_real_type", "amount": 10},
    )
    assert response.status_code == 400
    assert "Unsupported event type" in response.json()["detail"]


def test_strategy_selection_rules() -> None:
    temp = agent.analyze(_event(failure_reason="processor_timeout", previous_successes=5))
    assert temp.recommended_strategy == "retry_later"

    checkout = agent.analyze(
        _event(
            event_type="checkout_abandonment",
            failure_reason="cart_hesitation",
            checkout_visits=4,
            amount=60,
            cart_value=60,
        )
    )
    assert checkout.recommended_strategy == "send_checkout_reminder"

    low = agent.analyze(
        _event(
            failure_reason="plan_cancelled_intent",
            event_type="subscription_failure",
            previous_failures=7,
            retry_count=4,
            amount=119.99,
            subscription_age=10,
        )
    )
    assert low.recommended_strategy == "escalate_to_manual_review"
