"""Recovery agent orchestrator: detect → diagnose → score → choose strategy."""

from __future__ import annotations

from app.agent.detector import detect
from app.agent.diagnosis import diagnose
from app.agent.schemas import AnalysisResult, RecoveryEventInput
from app.agent.scoring import score
from app.agent.strategy import choose_strategy


class RecoveryAgent:
    """Coordinates the analysis pipeline. Does not execute actions."""

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

        return AnalysisResult(
            event=detected,
            detected_event_type=detected.event_type,
            diagnosis=diagnosis,
            recovery_probability=scored.probability,
            confidence=scored.confidence,
            recommended_strategy=strategy.strategy,
            reasoning=reasoning,
            score_factors=scored.factors,
            strategy_reason=strategy.reason,
        )


recovery_agent = RecoveryAgent()
