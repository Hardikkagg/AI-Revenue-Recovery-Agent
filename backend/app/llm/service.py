from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.agent.schemas import AnalysisResult

from app.config import settings
from app.llm.client import OllamaClient, OllamaClientError
from app.llm.prompts import SYSTEM_PROMPT, build_recovery_prompt
from app.llm.schemas import LLMGenerationResult

logger = logging.getLogger(__name__)



def generate_fallback_reasoning_and_message(analysis: AnalysisResult) -> tuple[str, str | None]:
    """Deterministic fallback templates when Ollama is unavailable or disabled."""
    event = analysis.event
    strategy = analysis.recommended_strategy
    prob = analysis.recovery_probability
    amount = event.amount

    # 1. Deterministic explanation
    reasoning = (
        f"Strategy '{strategy}' selected for customer #{event.customer_id} based on "
        f"diagnosis '{analysis.diagnosis.diagnosis_code}' and ML recovery probability of {prob:.2f}."
    )

    # 2. Customer message for communicative strategies
    customer_message: str | None = None
    if strategy == "send_checkout_reminder":
        cart = event.cart_value or amount
        customer_message = (
            f"Hi, we noticed you left items in your cart valued at ${cart:.2f}. "
            f"Your order is saved and ready for checkout whenever you'd like to complete it."
        )
    elif strategy == "send_subscription_update_request":
        customer_message = (
            f"We were unable to process your recurring payment of ${amount:.2f}. "
            f"Please update your billing details to ensure uninterrupted access."
        )
    elif strategy == "request_alternate_payment":
        customer_message = (
            f"We couldn't process your payment of ${amount:.2f} using your current method. "
            f"Please select or add an alternate payment method to complete this transaction."
        )

    return reasoning, customer_message


class LLMService:
    """Provides bounded LLM reasoning and communication generation with deterministic fallback."""

    def __init__(self, client: OllamaClient | None = None) -> None:
        self.client = client or OllamaClient()

    def generate_reasoning_and_message(self, analysis: AnalysisResult) -> LLMGenerationResult:
        """Generate structured reasoning and customer message for an analyzed recovery case."""
        # Check if LLM generation is globally enabled
        if not settings.enable_llm:
            reasoning, message = generate_fallback_reasoning_and_message(analysis)
            return LLMGenerationResult(
                provider="deterministic_fallback",
                model="template_v1",
                reasoning=reasoning,
                customer_message=message,
                fallback_used=True,
                fallback_reason="LLM generation disabled by configuration (ENABLE_LLM=false)",
            )

        try:
            prompt = build_recovery_prompt(analysis)
            response_data = self.client.generate(SYSTEM_PROMPT, prompt)

            reasoning = response_data.get("reasoning")
            customer_message = response_data.get("customer_message")

            if not reasoning:
                raise ValueError("LLM response did not contain 'reasoning' field")

            # Enforce safety guard: Non-communicative strategies must not send customer message
            if analysis.recommended_strategy in {"retry_now", "retry_later", "escalate_to_manual_review", "do_nothing"}:
                customer_message = None

            return LLMGenerationResult(
                provider="ollama",
                model=self.client.model,
                reasoning=reasoning,
                customer_message=customer_message,
                fallback_used=False,
            )

        except (OllamaClientError, ValueError, Exception) as exc:
            logger.warning("Ollama LLM generation failed (%s); falling back to deterministic templates", exc)
            reasoning, message = generate_fallback_reasoning_and_message(analysis)
            return LLMGenerationResult(
                provider="deterministic_fallback",
                model="template_v1",
                reasoning=reasoning,
                customer_message=message,
                fallback_used=True,
                fallback_reason=str(exc),
            )


llm_service = LLMService()
