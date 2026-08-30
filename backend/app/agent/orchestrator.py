"""Recovery agent orchestrator: detect → diagnose → score → choose strategy."""

from __future__ import annotations

from app.agent.detector import detect
from app.agent.diagnosis import diagnose
from app.agent.schemas import AnalysisResult, RecoveryEventInput
from app.agent.scoring import score
from app.agent.strategy import choose_strategy
from app.learning.policy import adaptive_policy
from app.llm import llm_service


class RecoveryAgent:
    """Coordinates the analysis pipeline: detect → diagnose → score → choose strategy → LLM reasoning."""

    def analyze(self, event: RecoveryEventInput) -> AnalysisResult:
        detected = detect(event)
        diagnosis = diagnose(detected)
        scored = score(detected, diagnosis)

        deterministic = choose_strategy(detected, diagnosis, scored)
        allowed = self._allowed_strategies(detected, diagnosis, scored)

        context = {
            "event_type": detected.event_type,
            "diagnosis_code": diagnosis.diagnosis_code,
            "payment_method": detected.payment_method,
            "probability_bucket": self._probability_bucket(scored.probability),
            "retry_bucket": self._retry_bucket(detected.retry_count),
        }

        strategy = deterministic
        policy_used = False
        if len(allowed) > 1:
            selected = adaptive_policy.select_strategy(
                context=context,
                allowed_strategies=allowed,
                deterministic_strategy=deterministic.strategy,
            )
            if selected in allowed:
                strategy = type(deterministic)(strategy=selected, reason=deterministic.reason)
                policy_used = selected != deterministic.strategy

        reasoning = [
            f"detected_event_type={detected.event_type}",
            f"diagnosis={diagnosis.diagnosis_code}: {diagnosis.diagnosis_text}",
            f"recoverability={diagnosis.recoverability}",
            f"recovery_probability={scored.probability:.4f}",
            f"confidence={scored.confidence}",
            f"recommended_strategy={strategy.strategy}",
            f"strategy_reason={strategy.reason}",
            f"adaptive_policy_used={str(policy_used).lower()}",
            f"allowed_strategies={allowed}",
            *scored.factors,
        ]

        partial_result = AnalysisResult(
            event=detected,
            detected_event_type=detected.event_type,
            diagnosis=diagnosis,
            recovery_probability=scored.probability,
            confidence=scored.confidence,
            recommended_strategy=strategy.strategy,
            reasoning=reasoning,
            score_factors=scored.factors,
            strategy_reason=strategy.reason,
            llm_generation=None,
        )

        # Generate bounded LLM reasoning and customer message (falls back safely if Ollama is unavailable)
        llm_gen = llm_service.generate_reasoning_and_message(partial_result)
        partial_result.llm_generation = llm_gen

        return partial_result

    def _allowed_strategies(self, event, diagnosis, score):
        """Return the set of strategies allowed by the hard safety/deterministic business rules."""
        deterministic = choose_strategy(event, diagnosis, score)
        allowed = [deterministic.strategy]

        if deterministic.strategy == "do_nothing":
            return ["do_nothing"]
        if deterministic.strategy == "escalate_to_manual_review":
            return ["escalate_to_manual_review"]

        if event.event_type == "payment_failure":
            if diagnosis.diagnosis_code == "temporary_payment_issue":
                allowed = ["retry_later", "request_alternate_payment"]
            elif diagnosis.diagnosis_code == "insufficient_funds":
                allowed = ["retry_later", "request_alternate_payment"]
            elif diagnosis.diagnosis_code == "card_declined":
                allowed = ["retry_later", "request_alternate_payment"]
            else:
                allowed = ["retry_now", "retry_later", "request_alternate_payment"]
        elif event.event_type == "checkout_abandonment":
            allowed = ["send_checkout_reminder", "do_nothing"]
        elif event.event_type == "subscription_failure":
            allowed = ["send_subscription_update_request", "retry_later", "escalate_to_manual_review"]

        return allowed

    def _probability_bucket(self, probability: float) -> str:
        if probability < 0.35:
            return "low"
        if probability < 0.60:
            return "medium"
        return "high"

    def _retry_bucket(self, retry_count: int) -> str:
        if retry_count <= 1:
            return "low"
        if retry_count <= 3:
            return "medium"
        return "high"


recovery_agent = RecoveryAgent()

