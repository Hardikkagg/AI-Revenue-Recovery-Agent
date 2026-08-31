"""Tests for adaptive learning, feedback validation, and safe candidate promotion."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

from app.agent.orchestrator import recovery_agent
from app.agent.predictor import CATEGORICAL_FEATURES, NUMERICAL_FEATURES, MLPredictor, ml_predictor
from app.agent.schemas import RecoveryEventInput
from app.database import Base, engine, get_db
from app.learning.policy import AdaptiveStrategyPolicy
from app.learning.retrainer import ModelRetrainer
from app.learning.schemas import LearningFeedback
from app.learning.service import (
    LEAKAGE_FIELDS,
    LearningService,
    build_learning_feedback,
    calculate_reward,
    validate_feedback_record,
)
from app.main import app
from app.models import Action, Customer, Event, RecoveryCase
from app.simulation.engine import RecoverySimulationEngine

GROUP_A_FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def clean_db():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        db.query(Action).delete()
        db.query(Event).delete()
        db.query(RecoveryCase).delete()
        db.query(Customer).delete()
        db.commit()
        yield db
    finally:
        db.close()


def _payment_event(customer_id: int, **overrides) -> RecoveryEventInput:
    payload = {
        "customer_id": customer_id,
        "event_type": "payment_failure",
        "amount": 175.50,
        "payment_method": "card",
        "failure_reason": "insufficient_funds",
        "customer_age": 42,
        "account_age": 365,
        "previous_successes": 12,
        "previous_failures": 1,
        "retry_count": 1,
        "checkout_visits": 0,
        "cart_value": 0.0,
        "subscription_age": 0,
    }
    payload.update(overrides)
    return RecoveryEventInput(**payload)


def test_simulation_persists_complete_group_a_features(clean_db):
    engine_sim = RecoverySimulationEngine()
    analysis = recovery_agent.analyze(_payment_event(501))
    engine_sim.execute(analysis, db=clean_db)

    ev = clean_db.query(Event).first()
    assert ev is not None
    details = json.loads(ev.details)

    for feat in GROUP_A_FEATURES:
        assert feat in details
        assert details[feat] is not None

    assert "diagnosis" in details
    assert "recovery_probability" in details
    assert details["selected_strategy"] == analysis.recommended_strategy


def test_learning_service_metrics_aggregation(clean_db):
    engine_sim = RecoverySimulationEngine()
    learning = LearningService()

    events = [
        _payment_event(601, amount=100.0, failure_reason="network_error"),
        RecoveryEventInput(
            customer_id=602,
            event_type="checkout_abandonment",
            amount=200.0,
            payment_method="card",
            failure_reason="cart_hesitation",
            customer_age=30,
            checkout_visits=4,
            cart_value=200.0,
        ),
        _payment_event(603, amount=300.0, failure_reason="fraud_hold"),
    ]
    for ev in events:
        analysis = recovery_agent.analyze(ev)
        engine_sim.execute(analysis, db=clean_db)

    metrics = learning.get_metrics(clean_db)

    assert metrics.total_cases == 3
    assert metrics.total_revenue_at_risk == 600.0
    assert 0.0 <= metrics.total_revenue_recovered <= 600.0
    assert len(metrics.strategy_breakdown) >= 2
    assert metrics.feedback_samples_count == 3


def test_extract_feedback_dataframe_has_zero_target_leakage(clean_db):
    engine_sim = RecoverySimulationEngine()
    learning = LearningService()
    event_input = RecoveryEventInput(
        customer_id=701,
        event_type="checkout_abandonment",
        amount=85.00,
        payment_method="card",
        failure_reason="cart_hesitation",
        customer_age=28,
        checkout_visits=3,
        cart_value=85.00,
    )
    analysis = recovery_agent.analyze(event_input)
    engine_sim.execute(analysis, db=clean_db)

    df = learning.extract_feedback_dataframe(clean_db)
    assert len(df) == 1
    assert set(df.columns) == set(GROUP_A_FEATURES + ["recovered"])

    for col in list(LEAKAGE_FIELDS) + ["diagnosis", "recovery_probability", "selected_strategy"]:
        assert col not in df.columns


def test_calculate_reward_full_partial_failed_and_zero_amount():
    assert calculate_reward(100.0, 100.0) == 1.0
    assert calculate_reward(100.0, 40.0) == 0.4
    assert calculate_reward(100.0, 0.0) == 0.0
    assert calculate_reward(0.0, 50.0) == 0.0
    assert calculate_reward(100.0, -10.0) == 0.0


def test_calculate_reward_clamps_excess_recovered_amount():
    assert calculate_reward(100.0, 150.0) == 1.0


def test_build_learning_feedback_contains_strategy_and_outcome():
    analysis = recovery_agent.analyze(_payment_event(720, failure_reason="network_error"))
    sim = RecoverySimulationEngine().execute(analysis)
    feedback = build_learning_feedback(sim, analysis.event)

    assert isinstance(feedback, LearningFeedback)
    assert feedback.strategy == analysis.recommended_strategy
    assert feedback.outcome == sim.outcome
    assert feedback.simulation_id == sim.simulation_id
    assert feedback.reward == calculate_reward(sim.amount_at_risk, sim.recovered_amount)
    assert feedback.amount_at_risk == sim.amount_at_risk
    assert feedback.customer_id == analysis.event.customer_id
    assert feedback.event_id == analysis.event.event_id


def test_learning_feedback_is_not_in_ml_feature_set(clean_db):
    engine_sim = RecoverySimulationEngine()
    analysis = recovery_agent.analyze(_payment_event(730, failure_reason="network_error"))
    engine_sim.execute(analysis, db=clean_db)

    recorded = clean_db.query(Action).first()
    assert recorded is not None
    payload = json.loads(recorded.details)
    assert "learning_feedback" in payload
    assert payload["learning_feedback"]["outcome"] == payload["outcome"]
    assert "reward" in payload["learning_feedback"]
    assert "recovered_amount" in payload

    df = LearningService().extract_feedback_dataframe(clean_db)
    assert set(df.columns) == set(GROUP_A_FEATURES + ["recovered"])
    assert "reward" not in df.columns
    assert "outcome" not in df.columns
    assert "strategy" not in df.columns


def test_feedback_validation_rejects_invalid_records():
    valid = {
        "amount": 50.0,
        "customer_age": 40,
        "account_age": 100,
        "previous_successes": 1,
        "previous_failures": 0,
        "retry_count": 0,
        "checkout_visits": 0,
        "cart_value": 0.0,
        "subscription_age": 0,
        "event_type": "payment_failure",
        "payment_method": "card",
        "failure_reason": "insufficient_funds",
    }
    ok = validate_feedback_record(valid, {"recovered": True, "recovered_amount": 50.0}, 50.0)
    assert ok is not None
    assert ok["recovered"] == 1
    assert set(ok.keys()) == set(GROUP_A_FEATURES + ["recovered"])

    missing = dict(valid)
    del missing["customer_age"]
    assert validate_feedback_record(missing, {"recovered": True, "recovered_amount": 50.0}, 50.0) is None

    assert validate_feedback_record(valid, {"recovered": "maybe", "recovered_amount": 50.0}, 50.0) is None
    assert validate_feedback_record(valid, {"recovered": True, "recovered_amount": 80.0}, 50.0) is None
    assert validate_feedback_record(valid, {"recovered": False, "recovered_amount": 10.0}, 50.0) is None
    assert validate_feedback_record(valid, {"recovered": True, "recovered_amount": -1.0}, 50.0) is None
    assert validate_feedback_record("not-json", {"recovered": True}, 50.0) is None


def test_feedback_dataset_generation_from_simulation(clean_db):
    engine_sim = RecoverySimulationEngine()
    learning = LearningService()
    analysis = recovery_agent.analyze(_payment_event(710, failure_reason="network_error"))
    engine_sim.execute(analysis, db=clean_db)

    df, rejected = learning.extract_feedback_dataset(clean_db)
    assert len(df) == 1
    assert rejected == 0
    assert df.iloc[0]["event_type"] == "payment_failure"
    assert df.iloc[0]["recovered"] in (0, 1)


def test_candidate_retraining_and_predictor_reload(clean_db, tmp_path):
    engine_sim = RecoverySimulationEngine()
    retrainer = ModelRetrainer()
    original_available = ml_predictor.is_available

    for ev in (
        _payment_event(801, failure_reason="network_error"),
        RecoveryEventInput(
            customer_id=802,
            event_type="subscription_failure",
            amount=45.0,
            payment_method="card",
            failure_reason="card_expired",
            customer_age=33,
            subscription_age=200,
        ),
    ):
        analysis = recovery_agent.analyze(ev)
        engine_sim.execute(analysis, db=clean_db)

    temp_prod = tmp_path / "prod_model.joblib"
    temp_metrics = tmp_path / "prod_metrics.json"
    temp_candidate = tmp_path / "candidate_model.joblib"
    temp_metrics.write_text(
        json.dumps({"holdout_metrics": {"roc_auc": 0.50, "test_accuracy": 0.50}}),
        encoding="utf-8",
    )

    res = retrainer.retrain(
        db=clean_db,
        model_output_path=temp_prod,
        metrics_output_path=temp_metrics,
        candidate_model_path=temp_candidate,
    )

    assert res.success is True
    assert res.promoted is True
    assert res.live_feedback_samples == 2
    assert res.total_training_samples == res.baseline_samples + 2
    assert temp_candidate.exists()
    assert temp_prod.exists()
    assert "test_accuracy" in res.holdout_metrics
    assert ml_predictor.is_available is True

    loaded = MLPredictor(temp_prod)
    assert loaded.is_available is True
    ml_predictor.reload()
    assert ml_predictor.is_available == original_available or ml_predictor.is_available is True


def test_safe_rejection_retains_current_model(clean_db, tmp_path):
    engine_sim = RecoverySimulationEngine()
    retrainer = ModelRetrainer()
    analysis = recovery_agent.analyze(_payment_event(811, failure_reason="network_error"))
    engine_sim.execute(analysis, db=clean_db)

    sentinel = tmp_path / "prod_model.joblib"
    sentinel.write_bytes(b"original-production-model")
    temp_metrics = tmp_path / "prod_metrics.json"
    temp_metrics.write_text(
        json.dumps({"holdout_metrics": {"roc_auc": 0.99, "test_accuracy": 0.99}}),
        encoding="utf-8",
    )
    candidate = tmp_path / "candidate.joblib"

    res = retrainer.retrain(
        db=clean_db,
        model_output_path=sentinel,
        metrics_output_path=temp_metrics,
        candidate_model_path=candidate,
        force_reject=True,
    )

    assert res.success is True
    assert res.promoted is False
    assert sentinel.read_bytes() == b"original-production-model"
    assert candidate.exists()
    assert "retained" in res.message.lower()


def test_predictor_reload_keeps_working_model_when_new_file_missing(tmp_path):
    predictor = MLPredictor()
    assert predictor.is_available is True
    assert predictor.reload(tmp_path / "does-not-exist.joblib") is False
    assert predictor.is_available is True


def test_predictor_explicit_missing_file_uses_fallback(tmp_path):
    predictor = MLPredictor(tmp_path / "does-not-exist.joblib")
    assert predictor.is_available is False
    assert predictor.reload(tmp_path / "still-missing.joblib") is False
    assert predictor.is_available is False


def test_api_metrics_endpoint(client, clean_db):
    payload = {
        "customer_id": 901,
        "event_type": "payment_failure",
        "amount": 125.0,
        "payment_method": "card",
        "failure_reason": "network_error",
        "customer_age": 41,
    }
    sim = client.post("/recovery/simulate", json=payload)
    assert sim.status_code == 200

    response = client.get("/recovery/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_cases" in data
    assert "overall_recovery_rate" in data
    assert "total_revenue_recovered" in data
    assert "strategy_breakdown" in data
    assert data["total_cases"] >= 1


def test_api_retrain_endpoint_does_not_require_breaking_existing_schemas(client, clean_db, tmp_path):
    analyze = client.post(
        "/recovery/analyze",
        json={
            "customer_id": 910,
            "event_type": "payment_failure",
            "amount": 80.0,
            "payment_method": "card",
            "failure_reason": "network_error",
        },
    )
    assert analyze.status_code == 200
    assert "recommended_strategy" in analyze.json()

    prod = tmp_path / "recovery_model.joblib"
    metrics = tmp_path / "model_metrics.json"
    candidate = tmp_path / "candidate_recovery_model.joblib"
    metrics.write_text(
        json.dumps({"holdout_metrics": {"roc_auc": 0.50, "test_accuracy": 0.50}}),
        encoding="utf-8",
    )

    with patch("app.learning.retrainer.DEFAULT_MODEL_PATH", prod), patch(
        "app.learning.retrainer.DEFAULT_METRICS_PATH", metrics
    ), patch("app.learning.retrainer.DEFAULT_CANDIDATE_MODEL_PATH", candidate):
        response = client.post("/recovery/retrain")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "promoted" in data
    assert "baseline_samples" in data
    assert "holdout_metrics" in data
    assert "cross_validation_5fold" in data
    ml_predictor.reload()


def test_adaptive_policy_returns_valid_strategy():
    policy = AdaptiveStrategyPolicy(seed=7)
    allowed = ["retry_later", "request_alternate_payment"]
    selected = policy.select_strategy(
        context={
            "event_type": "payment_failure",
            "diagnosis_code": "temporary_payment_issue",
            "payment_method": "card",
            "probability_bucket": "medium",
            "retry_bucket": "low",
        },
        allowed_strategies=allowed,
        deterministic_strategy="retry_later",
    )
    assert selected in allowed


def test_adaptive_policy_only_selects_allowed_strategies():
    policy = AdaptiveStrategyPolicy(seed=11)
    selected = policy.select_strategy(
        context={
            "event_type": "payment_failure",
            "diagnosis_code": "insufficient_funds",
            "payment_method": "card",
            "probability_bucket": "low",
            "retry_bucket": "medium",
        },
        allowed_strategies=["retry_later"],
        deterministic_strategy="retry_later",
    )
    assert selected == "retry_later"


def test_adaptive_policy_uses_deterministic_fallback_without_history():
    policy = AdaptiveStrategyPolicy(seed=13)
    selected = policy.select_strategy(
        context={
            "event_type": "checkout_abandonment",
            "diagnosis_code": "recoverable",
            "payment_method": "card",
            "probability_bucket": "high",
            "retry_bucket": "low",
        },
        allowed_strategies=["send_checkout_reminder", "do_nothing"],
        deterministic_strategy="send_checkout_reminder",
    )
    assert selected == "send_checkout_reminder"


def test_adaptive_policy_exploits_favoring_strategy():
    policy = AdaptiveStrategyPolicy(seed=17, epsilon=0.0)
    context = {
        "event_type": "payment_failure",
        "diagnosis_code": "temporary_payment_issue",
        "payment_method": "card",
        "probability_bucket": "medium",
        "retry_bucket": "low",
    }
    policy.update_from_feedback(
        context=context,
        strategy="request_alternate_payment",
        reward=1.0,
    )
    policy.update_from_feedback(
        context=context,
        strategy="request_alternate_payment",
        reward=0.9,
    )
    policy.update_from_feedback(
        context=context,
        strategy="retry_later",
        reward=0.1,
    )
    selected = policy.select_strategy(
        context=context,
        allowed_strategies=["retry_later", "request_alternate_payment"],
        deterministic_strategy="retry_later",
    )
    assert selected == "request_alternate_payment"


def test_adaptive_policy_epsilon_exploration_is_seeded_and_reproducible():
    policy = AdaptiveStrategyPolicy(seed=29, epsilon=1.0)
    results = [
        policy.select_strategy(
            context={
                "event_type": "payment_failure",
                "diagnosis_code": "temporary_payment_issue",
                "payment_method": "card",
                "probability_bucket": "medium",
                "retry_bucket": "low",
            },
            allowed_strategies=["retry_later", "request_alternate_payment"],
            deterministic_strategy="retry_later",
        )
        for _ in range(5)
    ]
    policy2 = AdaptiveStrategyPolicy(seed=29, epsilon=1.0)
    results2 = [
        policy2.select_strategy(
            context={
                "event_type": "payment_failure",
                "diagnosis_code": "temporary_payment_issue",
                "payment_method": "card",
                "probability_bucket": "medium",
                "retry_bucket": "low",
            },
            allowed_strategies=["retry_later", "request_alternate_payment"],
            deterministic_strategy="retry_later",
        )
        for _ in range(5)
    ]
    assert results == results2


def test_adaptive_policy_ignores_post_outcome_fields_in_context():
    policy = AdaptiveStrategyPolicy(seed=31)
    context_a = {
        "event_type": "payment_failure",
        "diagnosis_code": "temporary_payment_issue",
        "payment_method": "card",
        "probability_bucket": "medium",
        "retry_bucket": "low",
    }
    context_b = {
        **context_a,
        "outcome": "payment_recovered",
        "reward": 1.0,
        "recovered_amount": 100.0,
    }
    assert policy.build_context_key(context_a) == policy.build_context_key(context_b)


def test_simulation_updates_adaptive_policy_after_outcome():
    from app.simulation import engine as sim_engine_module

    policy = AdaptiveStrategyPolicy(seed=77, epsilon=0.0)
    with patch.object(sim_engine_module, "adaptive_policy", policy):
        analysis = recovery_agent.analyze(_payment_event(910, failure_reason="network_error"))
        sim = sim_engine_module.simulation_engine.execute(analysis)

        context = {
            "event_type": analysis.event.event_type,
            "diagnosis_code": analysis.diagnosis.diagnosis_code,
            "payment_method": analysis.event.payment_method,
            "probability_bucket": (
                "low" if analysis.recovery_probability < 0.35 else "medium" if analysis.recovery_probability < 0.60 else "high"
            ),
            "retry_bucket": (
                "low" if analysis.event.retry_count <= 1 else "medium" if analysis.event.retry_count <= 3 else "high"
            ),
        }

        assert sim.strategy in policy._stats.get(policy.build_context_key(context), {})
        assert policy.get_strategy_reward(context, sim.strategy) >= 0.0
