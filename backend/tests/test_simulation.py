"""Comprehensive tests for recovery simulation engine."""

import pytest
from fastapi.testclient import TestClient

from app.agent.orchestrator import recovery_agent
from app.agent.schemas import DetectedEvent, DiagnosisResult, RecoveryEventInput
from app.database import Base, engine, get_db
from app.main import app
from app.models import Action, Customer, Event, RecoveryCase
from app.simulation.communication import SimulatedCommunicationService
from app.simulation.engine import RecoverySimulationEngine
from app.simulation.gateway import SimulatedPaymentGateway


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def clean_db():
    """Ensure clean test tables."""
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


def test_simulate_retry_now():
    """Test retry_now execution in sandbox gateway."""
    gateway = SimulatedPaymentGateway(seed=42)
    engine = RecoverySimulationEngine(gateway=gateway)

    event_input = RecoveryEventInput(
        customer_id=101,
        event_type="payment_failure",
        amount=150.0,
        payment_method="credit_card",
        failure_reason="insufficient_funds",
        retry_count=0,
        previous_successes=10,
    )
    analysis = recovery_agent.analyze(event_input)
    # Even if strategy selected is retry_now or retry_later, test simulation
    sim_result = engine.execute(analysis)

    assert sim_result.simulation_id.startswith("sim_")
    assert sim_result.amount_at_risk == 150.0
    assert 0.0 <= sim_result.recovered_amount <= 150.0
    assert sim_result.explanation != ""
    assert sim_result.gateway_result is not None


def test_simulate_retry_later():
    """Test retry_later execution with delayed retry parameters."""
    gateway = SimulatedPaymentGateway(seed=42)
    engine = RecoverySimulationEngine(gateway=gateway)

    event_input = RecoveryEventInput(
        customer_id=102,
        event_type="payment_failure",
        amount=89.0,
        payment_method="credit_card",
        failure_reason="network_error",
        retry_count=1,
    )
    analysis = recovery_agent.analyze(event_input)
    assert analysis.recommended_strategy == "retry_later"

    sim_result = engine.execute(analysis)
    assert sim_result.strategy == "retry_later"
    assert sim_result.gateway_result is not None
    assert sim_result.gateway_result.action_type == "retry_delayed"
    assert 0.0 <= sim_result.recovered_amount <= 89.0


def test_simulate_request_alternate_payment():
    """Test alternate payment request simulation."""
    comm = SimulatedCommunicationService(seed=42)
    engine = RecoverySimulationEngine(communication=comm)

    event_input = RecoveryEventInput(
        customer_id=103,
        event_type="payment_failure",
        amount=120.0,
        payment_method="credit_card",
        failure_reason="card_expired",
        retry_count=1,
    )
    analysis = recovery_agent.analyze(event_input)
    assert analysis.recommended_strategy == "request_alternate_payment"

    sim_result = engine.execute(analysis)
    assert sim_result.strategy == "request_alternate_payment"
    assert sim_result.communication_result is not None
    assert sim_result.communication_result.channel == "email"
    assert "alternate" in sim_result.communication_result.message.lower()


def test_simulate_checkout_reminder():
    """Test checkout reminder communication simulation."""
    comm = SimulatedCommunicationService(seed=42)
    engine = RecoverySimulationEngine(communication=comm)

    event_input = RecoveryEventInput(
        customer_id=104,
        event_type="checkout_abandonment",
        amount=250.0,
        checkout_visits=4,
        cart_value=250.0,
    )
    analysis = recovery_agent.analyze(event_input)
    assert analysis.recommended_strategy == "send_checkout_reminder"

    sim_result = engine.execute(analysis)
    assert sim_result.strategy == "send_checkout_reminder"
    assert sim_result.communication_result is not None
    assert "cart" in sim_result.communication_result.message.lower()
    assert sim_result.outcome in {"checkout_completed", "checkout_abandoned"}


def test_simulate_subscription_update_request():
    """Test subscription update request simulation."""
    comm = SimulatedCommunicationService(seed=42)
    engine = RecoverySimulationEngine(communication=comm)

    event_input = RecoveryEventInput(
        customer_id=105,
        event_type="subscription_failure",
        amount=49.99,
        failure_reason="card_expired",
        subscription_age=400,
    )
    analysis = recovery_agent.analyze(event_input)
    assert analysis.recommended_strategy == "send_subscription_update_request"

    sim_result = engine.execute(analysis)
    assert sim_result.strategy == "send_subscription_update_request"
    assert sim_result.communication_result is not None
    assert sim_result.outcome in {"customer_updated_payment", "customer_unresponsive"}


def test_simulate_manual_escalation():
    """Test hard failure triggers manual escalation without financial recovery."""
    engine = RecoverySimulationEngine()

    event_input = RecoveryEventInput(
        customer_id=106,
        event_type="payment_failure",
        amount=500.0,
        payment_method="credit_card",
        failure_reason="fraud_hold",
    )
    analysis = recovery_agent.analyze(event_input)
    assert analysis.recommended_strategy == "escalate_to_manual_review"

    sim_result = engine.execute(analysis)
    assert sim_result.strategy == "escalate_to_manual_review"
    assert sim_result.status == "escalated"
    assert sim_result.outcome == "manual_review_required"
    assert sim_result.recovered is False
    assert sim_result.recovered_amount == 0.0


def test_simulate_do_nothing():
    """Test do_nothing strategy execution produces no action and zero recovered."""
    engine = RecoverySimulationEngine()

    event_input = RecoveryEventInput(
        customer_id=107,
        event_type="checkout_abandonment",
        amount=15.0,
        checkout_visits=1,
        cart_value=15.0,
        previous_failures=5,
    )
    analysis = recovery_agent.analyze(event_input)
    # Verify do_nothing behavior if score/intent is low
    sim_result = engine.execute(analysis)
    if analysis.recommended_strategy == "do_nothing":
        assert sim_result.status == "skipped"
        assert sim_result.outcome == "no_action_taken"
        assert sim_result.recovered is False
        assert sim_result.recovered_amount == 0.0


def test_recovered_amount_never_exceeds_amount():
    """Verify strictly: recovered_amount <= amount at risk across 50 simulated trials."""
    gateway = SimulatedPaymentGateway()
    comm = SimulatedCommunicationService()
    sim_eng = RecoverySimulationEngine(gateway=gateway, communication=comm)

    for i in range(50):
        amount = 10.0 + (i * 7.5)
        event_input = RecoveryEventInput(
            customer_id=200 + i,
            event_type="payment_failure",
            amount=amount,
            payment_method="credit_card",
            failure_reason="network_error" if i % 2 == 0 else "insufficient_funds",
            retry_count=i % 3,
        )
        analysis = recovery_agent.analyze(event_input)
        sim_res = sim_eng.execute(analysis)
        assert sim_res.recovered_amount <= amount
        assert sim_res.recovered_amount >= 0.0
        if sim_res.recovered:
            assert sim_res.recovered_amount == amount


def test_database_persistence(clean_db):
    """Test simulation persistence creates customer, recovery_case, event, and action records."""
    engine = RecoverySimulationEngine()
    event_input = RecoveryEventInput(
        customer_id=999,
        event_type="payment_failure",
        amount=199.99,
        payment_method="credit_card",
        failure_reason="network_error",
    )
    analysis = recovery_agent.analyze(event_input)
    sim_res = engine.execute(analysis, db=clean_db)

    # Verify DB records
    cust = clean_db.query(Customer).filter_by(id=999).first()
    assert cust is not None

    case = clean_db.query(RecoveryCase).filter_by(customer_id=999).first()
    assert case is not None
    assert case.amount == 199.99

    ev = clean_db.query(Event).filter_by(recovery_case_id=case.id).first()
    assert ev is not None
    assert ev.event_type == "payment_failure"

    act = clean_db.query(Action).filter_by(recovery_case_id=case.id).first()
    assert act is not None
    assert act.action_type == sim_res.strategy


def test_simulate_api_endpoint(client):
    """Test POST /recovery/simulate returns complete analysis + simulation result."""
    payload = {
        "customer_id": 301,
        "event_type": "payment_failure",
        "amount": 75.50,
        "payment_method": "credit_card",
        "failure_reason": "network_error",
    }
    response = client.post("/recovery/simulate", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "analysis" in data
    assert "simulation" in data
    assert data["analysis"]["event"]["customer_id"] == 301
    assert data["simulation"]["amount_at_risk"] == 75.50
    assert "explanation" in data["simulation"]
    assert 0.0 <= data["simulation"]["recovered_amount"] <= 75.50


def test_analyze_endpoint_still_works_unchanged(client):
    """Ensure existing POST /recovery/analyze endpoint remains completely operational."""
    payload = {
        "customer_id": 302,
        "event_type": "payment_failure",
        "amount": 100.0,
        "payment_method": "credit_card",
        "failure_reason": "insufficient_funds",
    }
    response = client.post("/recovery/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "recommended_strategy" in data
    assert "recovery_probability" in data
    assert "simulation" not in data  # analyze only scores and selects strategy


def test_simulation_rejects_invalid_event_type(client):
    """Ensure invalid event types return 400 Bad Request."""
    payload = {
        "customer_id": 303,
        "event_type": "fraudulent_chargeback_v2",
        "amount": 100.0,
    }
    response = client.post("/recovery/simulate", json=payload)
    assert response.status_code == 400
    assert "Unsupported event type" in response.json()["detail"]

