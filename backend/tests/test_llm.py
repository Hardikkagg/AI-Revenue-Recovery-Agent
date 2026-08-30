"""Comprehensive unit and integration test suite for LLM reasoning and message generation."""

import json
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.agent.orchestrator import recovery_agent
from app.agent.schemas import AnalysisResult, RecoveryEventInput
from app.config import settings
from app.llm.client import OllamaClient, OllamaClientError
from app.llm.prompts import SYSTEM_PROMPT, build_recovery_prompt
from app.llm.schemas import LLMGenerationResult
from app.llm.service import LLMService, generate_fallback_reasoning_and_message
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_build_recovery_prompt_structure():
    """Verify prompt builder formats pre-execution context safely and omits post-outcome fields."""
    event_input = RecoveryEventInput(
        customer_id=101,
        event_type="payment_failure",
        amount=149.99,
        payment_method="credit_card",
        failure_reason="network_error",
        retry_count=0,
    )
    analysis = recovery_agent.analyze(event_input)
    prompt = build_recovery_prompt(analysis)

    assert "Input Recovery Context:" in prompt
    assert '"event_type": "payment_failure"' in prompt
    assert '"amount": 149.99' in prompt
    assert '"recovered_amount"' not in prompt
    assert '"recovered"' not in prompt
    assert '"chosen_strategy"' in prompt


def test_llm_service_with_mocked_ollama_success():
    """Test LLM service with successful Ollama response."""
    mock_client = MagicMock(spec=OllamaClient)
    mock_client.model = "llama3.2"
    mock_client.generate.return_value = {
        "reasoning": "Transient bank connectivity timeout warrants a delayed retry attempt.",
        "customer_message": None,
    }

    service = LLMService(client=mock_client)
    event_input = RecoveryEventInput(
        customer_id=102,
        event_type="payment_failure",
        amount=89.00,
        payment_method="credit_card",
        failure_reason="network_error",
    )
    analysis = recovery_agent.analyze(event_input)
    result = service.generate_reasoning_and_message(analysis)

    assert result.provider == "ollama"
    assert result.model == "llama3.2"
    assert "connectivity timeout" in result.reasoning
    assert result.customer_message is None
    assert result.fallback_used is False


def test_llm_fallback_when_ollama_fails():
    """Test graceful fallback to deterministic templates when Ollama connection fails."""
    mock_client = MagicMock(spec=OllamaClient)
    mock_client.model = "llama3.2"
    mock_client.generate.side_effect = OllamaClientError("Failed to connect to Ollama at http://localhost:11434")

    service = LLMService(client=mock_client)
    event_input = RecoveryEventInput(
        customer_id=103,
        event_type="checkout_abandonment",
        amount=199.99,
        checkout_visits=3,
        cart_value=199.99,
    )
    analysis = recovery_agent.analyze(event_input)
    result = service.generate_reasoning_and_message(analysis)

    assert result.provider == "deterministic_fallback"
    assert result.model == "template_v1"
    assert result.fallback_used is True
    assert "Failed to connect to Ollama" in (result.fallback_reason or "")
    assert result.customer_message is not None
    assert "cart" in result.customer_message.lower()


def test_llm_fallback_when_disabled_in_config():
    """Test that disabling ENABLE_LLM directly routes to deterministic templates."""
    with patch.object(settings, "enable_llm", False):
        service = LLMService()
        event_input = RecoveryEventInput(
            customer_id=104,
            event_type="subscription_failure",
            amount=29.99,
            failure_reason="card_expired",
            subscription_age=120,
        )
        analysis = recovery_agent.analyze(event_input)
        result = service.generate_reasoning_and_message(analysis)

        assert result.provider == "deterministic_fallback"
        assert result.fallback_used is True
        assert "ENABLE_LLM=false" in (result.fallback_reason or "")
        assert result.customer_message is not None
        assert "recurring payment" in result.customer_message.lower()


def test_customer_message_does_not_expose_ml_probability_or_technical_internals():
    """Verify customer-facing communications never leak raw ML probabilities or model names."""
    event_input = RecoveryEventInput(
        customer_id=105,
        event_type="checkout_abandonment",
        amount=99.00,
        checkout_visits=4,
        cart_value=99.00,
    )
    analysis = recovery_agent.analyze(event_input)
    _, message = generate_fallback_reasoning_and_message(analysis)

    assert message is not None
    forbidden_tokens = ["probability", "score", "ml", "logistic", "algorithm", "ai model", "feature_weight"]
    for token in forbidden_tokens:
        assert token not in message.lower(), f"Customer message leaked forbidden internal token: '{token}'"



def test_customer_message_does_not_claim_success_before_execution():
    """Verify communication does not assert payment has already succeeded."""
    event_input = RecoveryEventInput(
        customer_id=106,
        event_type="payment_failure",
        amount=50.00,
        payment_method="credit_card",
        failure_reason="card_expired",
    )
    analysis = recovery_agent.analyze(event_input)
    _, message = generate_fallback_reasoning_and_message(analysis)

    assert message is not None
    assert "payment successful" not in message.lower()
    assert "recovered" not in message.lower()
    assert "processed successfully" not in message.lower()


def test_llm_generation_cannot_override_strategy():
    """Verify that strategy selection remains 100% authoritative and unaltered by LLM output."""
    mock_client = MagicMock(spec=OllamaClient)
    mock_client.model = "llama3.2"
    # Even if LLM hallucinates an alternative strategy name in reasoning
    mock_client.generate.return_value = {
        "reasoning": "I think we should do something different.",
        "customer_message": "Hello customer",
    }

    service = LLMService(client=mock_client)
    event_input = RecoveryEventInput(
        customer_id=107,
        event_type="payment_failure",
        amount=75.00,
        payment_method="credit_card",
        failure_reason="fraud_hold",
    )
    analysis = recovery_agent.analyze(event_input)
    assert analysis.recommended_strategy == "escalate_to_manual_review"

    result = service.generate_reasoning_and_message(analysis)
    # Strategy on analysis is completely immutable by LLMService
    assert analysis.recommended_strategy == "escalate_to_manual_review"
    # For safety, manual escalation clears customer message
    assert result.customer_message is None


def test_payment_failure_message_generation():
    """Test customer message for payment_failure requiring alternate payment."""
    event_input = RecoveryEventInput(
        customer_id=108,
        event_type="payment_failure",
        amount=65.00,
        payment_method="credit_card",
        failure_reason="card_expired",
        retry_count=1,
    )
    analysis = recovery_agent.analyze(event_input)
    assert analysis.recommended_strategy == "request_alternate_payment"
    assert analysis.llm_generation is not None
    assert analysis.llm_generation.customer_message is not None
    assert "alternate payment" in analysis.llm_generation.customer_message.lower()


def test_checkout_abandonment_message_generation():
    """Test customer message for checkout abandonment reminder."""
    event_input = RecoveryEventInput(
        customer_id=109,
        event_type="checkout_abandonment",
        amount=129.50,
        checkout_visits=3,
        cart_value=129.50,
    )
    analysis = recovery_agent.analyze(event_input)
    assert analysis.recommended_strategy == "send_checkout_reminder"
    assert analysis.llm_generation is not None
    assert analysis.llm_generation.customer_message is not None
    assert "cart" in analysis.llm_generation.customer_message.lower()


def test_subscription_failure_message_generation():
    """Test customer message for subscription payment update request."""
    event_input = RecoveryEventInput(
        customer_id=110,
        event_type="subscription_failure",
        amount=39.99,
        failure_reason="card_expired",
        subscription_age=300,
    )
    analysis = recovery_agent.analyze(event_input)
    assert analysis.recommended_strategy == "send_subscription_update_request"
    assert analysis.llm_generation is not None
    assert analysis.llm_generation.customer_message is not None
    assert "billing" in analysis.llm_generation.customer_message.lower() or "payment" in analysis.llm_generation.customer_message.lower()


def test_analyze_endpoint_includes_llm_generation(client):
    """Test POST /recovery/analyze returns analysis along with structured llm_generation."""
    payload = {
        "customer_id": 201,
        "event_type": "checkout_abandonment",
        "amount": 80.00,
        "checkout_visits": 3,
        "cart_value": 80.00,
    }
    response = client.post("/recovery/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "llm_generation" in data
    assert data["llm_generation"]["provider"] in {"ollama", "deterministic_fallback"}
    assert "reasoning" in data["llm_generation"]


def test_simulate_endpoint_includes_llm_generation(client):
    """Test POST /recovery/simulate returns analysis with llm_generation alongside simulation."""
    payload = {
        "customer_id": 202,
        "event_type": "payment_failure",
        "amount": 95.00,
        "payment_method": "credit_card",
        "failure_reason": "network_error",
    }
    response = client.post("/recovery/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data
    assert "simulation" in data
    assert "llm_generation" in data["analysis"]
    assert data["analysis"]["llm_generation"] is not None
