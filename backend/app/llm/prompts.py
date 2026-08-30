"""Safe, bounded prompts for recovery reasoning and customer communication.

Safety constraints enforced:
1. The LLM must not change or override the chosen strategy.
2. The LLM must not make financial decisions or claim payments succeeded before execution.
3. The LLM must not expose internal ML probabilities or internal technical terms to customers.
4. The LLM must not invent discounts, refunds, guarantees, or unauthorized concessions.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.agent.schemas import AnalysisResult


SYSTEM_PROMPT = """You are a specialized enterprise reasoning and communication assistant for a revenue recovery platform.

CRITICAL CONSTRAINTS:
1. The recovery strategy has ALREADY BEEN DECIDED by deterministic rules and ML scoring. You CANNOT change or override the strategy.
2. You must produce two outputs in strict JSON format:
   - "reasoning": An internal 1-2 sentence executive explanation of WHY this specific strategy is appropriate given the event, failure diagnosis, and recovery context.
   - "customer_message": If the strategy involves customer communication (e.g. checkout reminder, update subscription payment, request alternate payment), provide a concise, friendly, empathetic 1-2 sentence message to the customer. If the strategy does NOT involve customer communication (e.g. retry_now, retry_later, escalate_to_manual_review, do_nothing), this field MUST be null.
3. STRICT COMMUNICATION RULES:
   - Do NOT mention "AI", "machine learning", "probability", "score", "ML", or internal algorithm names.
   - Do NOT claim that payment has already succeeded or that an action took place before execution.
   - Do NOT invent unauthorized discounts, promo codes, refunds, or waivers.
   - Keep messages professional, clear, and actionable.

Return ONLY a valid JSON object matching:
{
  "reasoning": "...",
  "customer_message": "..." or null
}
"""


def build_recovery_prompt(analysis: AnalysisResult) -> str:
    """Build bounded prompt payload for the LLM based strictly on pre-execution context."""
    event = analysis.event

    context = {
        "event_type": event.event_type,
        "amount": round(event.amount, 2),
        "failure_reason": event.failure_reason,
        "diagnosis_code": analysis.diagnosis.diagnosis_code,
        "diagnosis_text": analysis.diagnosis.diagnosis_text,
        "recoverability": analysis.diagnosis.recoverability,
        "recovery_probability": round(analysis.recovery_probability, 4),
        "chosen_strategy": analysis.recommended_strategy,
        "strategy_reason": analysis.strategy_reason,
        "customer_id": event.customer_id,
        "retry_count": event.retry_count,
        "previous_successes": event.previous_successes,
        "previous_failures": event.previous_failures,
        "checkout_visits": event.checkout_visits if event.event_type == "checkout_abandonment" else None,
        "cart_value": event.cart_value if event.event_type == "checkout_abandonment" else None,
        "subscription_age_days": event.subscription_age if event.event_type == "subscription_failure" else None,
    }

    # Clean out None values
    clean_context = {k: v for k, v in context.items() if v is not None}

    return (
        f"Input Recovery Context:\n"
        f"{json.dumps(clean_context, indent=2)}\n\n"
        f"Generate the structured JSON response for the decided strategy '{analysis.recommended_strategy}'."
    )
