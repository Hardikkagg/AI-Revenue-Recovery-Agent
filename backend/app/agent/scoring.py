"""Recovery-probability scorer using ML model with deterministic baseline fallback."""

from __future__ import annotations

from app.agent.predictor import ml_predictor
from app.agent.schemas import DetectedEvent, DiagnosisResult, ScoreResult

_TEMPORARY = {"network_error", "processor_timeout", "session_timeout"}
_FIXABLE = {"card_expired", "payment_form_dropoff", "insufficient_funds"}
_HARD = {"fraud_hold", "account_closed", "plan_cancelled_intent"}
_PRICE_FRICTION = {"shipping_cost", "comparison_shopping"}
_WALLETS = {"card", "paypal", "apple_pay", "google_pay"}


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)


def score_deterministic(event: DetectedEvent, diagnosis: DiagnosisResult) -> ScoreResult:
    """Return a deterministic baseline probability in [0, 1] plus confidence and factors."""
    probability = 0.42
    factors: list[str] = ["baseline_scorer=rule_based", "base_rate=0.42"]

    success_boost = min(event.previous_successes, 8) * 0.035
    if success_boost:
        probability += success_boost
        factors.append(f"previous_successes=+{success_boost:.3f}")

    failure_penalty = min(event.previous_failures, 8) * 0.045
    if failure_penalty:
        probability -= failure_penalty
        factors.append(f"previous_failures=-{failure_penalty:.3f}")

    retry_penalty = min(event.retry_count, 6) * 0.04
    if retry_penalty:
        probability -= retry_penalty
        factors.append(f"retry_count=-{retry_penalty:.3f}")

    if event.amount > 250:
        probability -= 0.08
        factors.append("high_amount=-0.080")
    elif event.amount < 40:
        probability += 0.04
        factors.append("low_amount=+0.040")

    reason = event.failure_reason
    if reason in _TEMPORARY:
        probability += 0.12
        factors.append("temporary_failure=+0.120")
    elif reason in _FIXABLE:
        probability += 0.07
        factors.append("fixable_reason=+0.070")
    elif reason in _HARD:
        probability -= 0.18
        factors.append("hard_failure=-0.180")
    elif reason in _PRICE_FRICTION:
        probability -= 0.07
        factors.append("price_friction=-0.070")

    if event.event_type == "checkout_abandonment" and event.checkout_visits >= 3:
        probability += 0.06
        factors.append("checkout_intent=+0.060")

    if event.event_type == "subscription_failure" and event.subscription_age >= 180:
        probability += 0.04
        factors.append("established_subscription=+0.040")

    if event.payment_method in _WALLETS:
        probability += 0.02
        factors.append("wallet_or_card=+0.020")
    elif event.payment_method in {"ach", "bank_transfer"}:
        probability -= 0.03
        factors.append("bank_method=-0.030")

    if diagnosis.recoverability == "unlikely":
        probability -= 0.08
        factors.append("diagnosis_unlikely=-0.080")
    elif diagnosis.recoverability == "recoverable":
        probability += 0.04
        factors.append("diagnosis_recoverable=+0.040")

    probability = _clamp(probability)

    strong = sum(
        1
        for item in factors
        if item.startswith(("temporary_failure", "hard_failure", "previous_failures", "previous_successes"))
    )
    if diagnosis.recoverability == "unlikely" or event.retry_count >= 4:
        confidence = "HIGH"
    elif strong >= 2 or diagnosis.recoverability == "recoverable":
        confidence = "HIGH"
    elif event.failure_reason == "unspecified":
        confidence = "LOW"
    else:
        confidence = "MEDIUM"

    return ScoreResult(probability=probability, confidence=confidence, factors=factors)


def score(
    event: DetectedEvent,
    diagnosis: DiagnosisResult,
    use_ml: bool = True,
) -> ScoreResult:
    """Score recovery probability using ML model when available, falling back to deterministic baseline."""
    if use_ml and ml_predictor.is_available:
        prediction = ml_predictor.predict(event)
        if prediction is not None:
            probability, ml_factors = prediction
            factors = ["ml_model=LogisticRegression", *ml_factors]

            if diagnosis.recoverability == "unlikely" or event.retry_count >= 4 or probability <= 0.20 or probability >= 0.75:
                confidence = "HIGH"
            elif event.failure_reason == "unspecified":
                confidence = "LOW"
            else:
                confidence = "MEDIUM"

            return ScoreResult(
                probability=probability,
                confidence=confidence,
                factors=factors,
            )

    return score_deterministic(event, diagnosis)

