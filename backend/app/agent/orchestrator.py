"""Recovery agent orchestrator: detect → diagnose → score → choose strategy."""

from __future__ import annotations

from app.agent.detector import detect
from app.agent.diagnosis import diagnose
from app.agent.schemas import AnalysisResult, RecoveryEventInput
from app.agent.scoring import score
from app.agent.strategy import choose_strategy
from app.llm import llm_service


class RecoveryAgent:
    """Coordinates the analysis pipeline: detect → diagnose → score → choose strategy → LLM reasoning."""

    def analyze(self, event: RecoveryEventInput) -> AnalysisResult:
        detected = detect(event)
        diagnosis = diagnose(detected)
        scored = score(detected, diagnosis)
        strategy = choose_strategy(detected, diagnosis, scored)

        reasoning = [
            f"detected_event_type={detected.event_type}",
            f"diagnosis={diagnosis.diagnosis_code}: {diagnosis.diagnosis_text}",
            f"recoverability={diagnosis.recoverability}",
            f"recovery_probability={scored.probability:.4f}",
            f"confidence={scored.confidence}",
            f"recommended_strategy={strategy.strategy}",
            f"strategy_reason={strategy.reason}",
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


recovery_agent = RecoveryAgent()

