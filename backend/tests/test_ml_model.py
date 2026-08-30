"""Tests for the supervised ML recovery probability model and predictor service."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.agent.detector import detect
from app.agent.diagnosis import diagnose
from app.agent.orchestrator import RecoveryAgent
from app.agent.predictor import MLPredictor, ml_predictor
from app.agent.schemas import RecoveryEventInput
from app.agent.scoring import score, score_deterministic
from app.main import app
from scripts.train_model import train_model

client = TestClient(app)
agent = RecoveryAgent()


def _event(**overrides) -> RecoveryEventInput:
    payload = {
        "customer_id": 101,
        "event_type": "payment_failure",
        "amount": 50.00,
        "payment_method": "card",
        "failure_reason": "network_error",
        "customer_age": 30,
        "account_age": 200,
        "previous_successes": 4,
        "previous_failures": 1,
        "retry_count": 0,
        "checkout_visits": 0,
        "cart_value": 0.0,
        "subscription_age": 0,
    }
    payload.update(overrides)
    return RecoveryEventInput(**payload)


def test_model_training_completes_and_creates_artifacts() -> None:
    """Verify training function produces model artifact and valid evaluation metrics."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_model = Path(tmp_dir) / "test_model.joblib"
        tmp_metrics = Path(tmp_dir) / "test_metrics.json"

        metrics = train_model(
            model_output_path=tmp_model,
            metrics_output_path=tmp_metrics,
        )

        assert tmp_model.exists()
        assert tmp_metrics.exists()
        assert 0.55 <= metrics["holdout_metrics"]["test_accuracy"] <= 0.75
        assert 0.55 <= metrics["holdout_metrics"]["roc_auc"] <= 0.75
        assert metrics["dataset_size"] == 2500
        assert "confusion_matrix" in metrics["holdout_metrics"]


def test_model_artifact_can_be_loaded() -> None:
    """Verify that the model was trained and loaded by the global predictor."""
    assert ml_predictor.is_available is True


def test_prediction_probability_is_between_zero_and_one() -> None:
    """Verify ML predictor outputs a valid probability bounded in [0, 1] and explainable factors."""
    event = detect(_event())
    prediction = ml_predictor.predict(event)
    assert prediction is not None

    prob, factors = prediction
    assert 0.0 <= prob <= 1.0
    assert isinstance(factors, list)
    assert len(factors) > 0
    assert any("=" in f for f in factors)


def test_prediction_works_for_payment_failure() -> None:
    """Verify prediction on representative payment_failure event."""
    event = detect(
        _event(
            event_type="payment_failure",
            failure_reason="network_error",
            previous_successes=5,
            amount=35.0,
        )
    )
    prediction = ml_predictor.predict(event)
    assert prediction is not None
    prob, factors = prediction
    assert prob > 0.50
    assert any("failure_reason_network_error" in f for f in factors)


def test_prediction_works_for_checkout_abandonment() -> None:
    """Verify prediction on representative checkout_abandonment event."""
    event = detect(
        _event(
            event_type="checkout_abandonment",
            failure_reason="payment_form_dropoff",
            checkout_visits=5,
            cart_value=88.0,
            amount=88.0,
        )
    )
    prediction = ml_predictor.predict(event)
    assert prediction is not None
    prob, factors = prediction
    assert prob > 0.50
    assert any("failure_reason_payment_form_dropoff" in f for f in factors)


def test_prediction_works_for_subscription_failure() -> None:
    """Verify prediction on representative subscription_failure event."""
    event = detect(
        _event(
            event_type="subscription_failure",
            failure_reason="dunning_unresponsive",
            subscription_age=400,
            retry_count=2,
            previous_successes=3,
        )
    )
    prediction = ml_predictor.predict(event)
    assert prediction is not None
    prob, factors = prediction
    assert 0.0 <= prob <= 1.0


def test_recovery_agent_uses_ml_model() -> None:
    """Verify RecoveryAgent incorporates ML model into its analysis results."""
    event = _event(failure_reason="network_error", previous_successes=6)
    result = agent.analyze(event)

    assert result.recovery_probability > 0.50
    assert any("ml_model=LogisticRegression" in f for f in result.score_factors)
    assert any("ml_model=LogisticRegression" in r for r in result.reasoning)


def test_fallback_to_deterministic_scorer_when_disabled() -> None:
    """Verify score() falls back to rule-based scoring when use_ml=False."""
    event = detect(_event())
    diagnosis = diagnose(event)

    ml_scored = score(event, diagnosis, use_ml=True)
    fallback_scored = score(event, diagnosis, use_ml=False)

    assert "ml_model=LogisticRegression" in ml_scored.factors
    assert "baseline_scorer=rule_based" in fallback_scored.factors
    assert 0.0 <= fallback_scored.probability <= 1.0


def test_fallback_when_model_file_missing() -> None:
    """Verify MLPredictor with invalid path fails gracefully and score() falls back."""
    dummy_predictor = MLPredictor(model_path="non_existent_model_file.joblib")
    assert dummy_predictor.is_available is False

    event = detect(_event())
    diagnosis = diagnose(event)
    fallback = score_deterministic(event, diagnosis)

    assert fallback.probability is not None
    assert "baseline_scorer=rule_based" in fallback.factors


def test_api_endpoint_with_ml_analysis() -> None:
    """Verify POST /recovery/analyze returns ML-backed probability and reasoning."""
    response = client.post(
        "/recovery/analyze",
        json={
            "customer_id": 42,
            "event_type": "subscription_failure",
            "amount": 79.99,
            "payment_method": "card",
            "failure_reason": "card_expired",
            "previous_successes": 5,
            "previous_failures": 0,
            "retry_count": 0,
            "subscription_age": 365,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["detected_event_type"] == "subscription_failure"
    assert data["diagnosis"]["diagnosis_code"] == "expired_card"
    assert data["recommended_strategy"] == "send_subscription_update_request"
    assert 0.0 <= data["recovery_probability"] <= 1.0
    assert any("ml_model=LogisticRegression" in f for f in data["score_factors"])


def test_api_rejects_invalid_event_type() -> None:
    """Verify POST /recovery/analyze rejects invalid event types with 400."""
    response = client.post(
        "/recovery/analyze",
        json={"customer_id": 1, "event_type": "unsupported_event", "amount": 10},
    )
    assert response.status_code == 400
    assert "Unsupported event type" in response.json()["detail"]
