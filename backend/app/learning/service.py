"""Learning Service: Aggregates performance metrics and extracts clean feedback data."""

from __future__ import annotations

import json
import logging
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.agent.predictor import CATEGORICAL_FEATURES, NUMERICAL_FEATURES
from app.agent.schemas import SUPPORTED_EVENT_TYPES
from app.learning.schemas import RecoveryMetricsResponse, StrategyPerformance
from app.models import Action, RecoveryCase

logger = logging.getLogger(__name__)

ALL_FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
TARGET_COLUMN = "recovered"
LEAKAGE_FIELDS = {
    "recovered_amount",
    "recovery_time",
    "outcome",
    "status",
    "gateway_reference",
    "customer_responded",
    "action_details",
    "explanation",
    "simulation_id",
    "customer_id",
    "event_id",
}
DECISION_CONTEXT_FIELDS = {"diagnosis", "recovery_probability", "selected_strategy"}


def _parse_recovered(value: Any) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)) and value in (0, 1, 0.0, 1.0):
        return int(value)
    if isinstance(value, str) and value.strip().lower() in {"true", "false", "0", "1", "yes", "no"}:
        return int(value.strip().lower() in {"true", "1", "yes"})
    return None


def validate_feedback_record(
    ev_data: dict[str, Any],
    act_data: dict[str, Any],
    case_amount: float,
) -> dict[str, Any] | None:
    """Return a training row or None if the record is invalid / leaky / incomplete."""
    if not isinstance(ev_data, dict) or not isinstance(act_data, dict):
        return None

    recovered = _parse_recovered(act_data.get("recovered"))
    if recovered is None:
        return None

    try:
        amount = float(ev_data.get("amount", case_amount))
    except (TypeError, ValueError):
        return None
    if amount <= 0:
        return None

    recovered_amount_raw = act_data.get("recovered_amount")
    if recovered_amount_raw is None:
        recovered_amount = amount if recovered else 0.0
    else:
        try:
            recovered_amount = float(recovered_amount_raw)
        except (TypeError, ValueError):
            return None

    if recovered_amount < 0 or recovered_amount > amount:
        return None
    if recovered == 0 and recovered_amount != 0:
        return None

    required = {
        "amount": amount,
        "customer_age": ev_data.get("customer_age"),
        "account_age": ev_data.get("account_age"),
        "previous_successes": ev_data.get("previous_successes"),
        "previous_failures": ev_data.get("previous_failures"),
        "retry_count": ev_data.get("retry_count"),
        "checkout_visits": ev_data.get("checkout_visits"),
        "cart_value": ev_data.get("cart_value"),
        "subscription_age": ev_data.get("subscription_age"),
        "event_type": ev_data.get("event_type"),
        "payment_method": ev_data.get("payment_method"),
        "failure_reason": ev_data.get("failure_reason"),
    }
    if any(value is None or value == "" for value in required.values()):
        return None

    event_type = str(required["event_type"]).strip().lower()
    if event_type not in SUPPORTED_EVENT_TYPES:
        return None

    try:
        row = {
            "amount": float(required["amount"]),
            "customer_age": int(required["customer_age"]),
            "account_age": int(required["account_age"]),
            "previous_successes": int(required["previous_successes"]),
            "previous_failures": int(required["previous_failures"]),
            "retry_count": int(required["retry_count"]),
            "checkout_visits": int(required["checkout_visits"]),
            "cart_value": float(required["cart_value"]),
            "subscription_age": int(required["subscription_age"]),
            "event_type": event_type,
            "payment_method": str(required["payment_method"]).strip().lower(),
            "failure_reason": str(required["failure_reason"]).strip().lower(),
            "recovered": recovered,
        }
    except (TypeError, ValueError):
        return None

    return row


class LearningService:
    """Aggregates recovery analytics and prepares verified feedback datasets for learning."""

    def get_metrics(self, db: Session) -> RecoveryMetricsResponse:
        """Compute holistic recovery metrics across all persisted cases, events, and actions."""
        cases = db.query(RecoveryCase).all()
        actions = db.query(Action).all()

        total_cases = len(cases)
        resolved_cases = sum(1 for c in cases if c.status == "resolved")
        escalated_cases = sum(1 for c in cases if c.status == "escalated")
        closed_cases = sum(1 for c in cases if c.status == "closed")

        total_revenue_at_risk = sum(c.amount for c in cases)
        total_revenue_recovered = 0.0

        strategy_stats: dict[str, dict[str, Any]] = {}
        feedback_count = 0

        for act in actions:
            strat = act.action_type
            if strat not in strategy_stats:
                strategy_stats[strat] = {
                    "total": 0,
                    "recovered_count": 0,
                    "failed_count": 0,
                    "at_risk": 0.0,
                    "recovered_amount": 0.0,
                }

            case = act.recovery_case
            case_amount = case.amount if case else 0.0
            strategy_stats[strat]["total"] += 1
            strategy_stats[strat]["at_risk"] += case_amount

            recovered = False
            rec_amount = 0.0
            if act.details:
                try:
                    det = json.loads(act.details)
                    recovered = bool(det.get("recovered", False))
                    rec_amount = float(det.get("recovered_amount", 0.0))
                    feedback_count += 1
                except Exception as exc:
                    logger.debug("Failed parsing action details (%s)", exc)

            if recovered:
                strategy_stats[strat]["recovered_count"] += 1
                strategy_stats[strat]["recovered_amount"] += rec_amount
                total_revenue_recovered += rec_amount
            else:
                strategy_stats[strat]["failed_count"] += 1

        strategy_breakdown = [
            StrategyPerformance(
                strategy=strat,
                total_cases=data["total"],
                successful_recoveries=data["recovered_count"],
                failed_cases=data["failed_count"],
                recovery_rate=round(data["recovered_count"] / max(1, data["total"]), 4),
                revenue_at_risk=round(data["at_risk"], 2),
                revenue_recovered=round(data["recovered_amount"], 2),
            )
            for strat, data in sorted(strategy_stats.items())
        ]

        overall_recovery_rate = (
            round(resolved_cases / max(1, total_cases), 4) if total_cases > 0 else 0.0
        )

        return RecoveryMetricsResponse(
            total_cases=total_cases,
            resolved_cases=resolved_cases,
            escalated_cases=escalated_cases,
            closed_cases=closed_cases,
            overall_recovery_rate=overall_recovery_rate,
            total_revenue_at_risk=round(total_revenue_at_risk, 2),
            total_revenue_recovered=round(total_revenue_recovered, 2),
            strategy_breakdown=strategy_breakdown,
            feedback_samples_count=feedback_count,
        )

    def extract_feedback_dataset(self, db: Session) -> tuple[pd.DataFrame, int]:
        """Return (valid training rows, rejected_count) with zero target leakage."""
        cases = db.query(RecoveryCase).all()
        rows: list[dict[str, Any]] = []
        rejected = 0
        seen_simulation_ids: set[str] = set()

        for case in cases:
            if not case.events or not case.actions:
                continue

            event_record = case.events[0]
            action_record = case.actions[0]

            if not event_record.details or not action_record.details:
                rejected += 1
                continue

            try:
                ev_data = json.loads(event_record.details)
                act_data = json.loads(action_record.details)
            except Exception:
                rejected += 1
                continue

            sim_id = str(act_data.get("simulation_id") or "")
            if sim_id:
                if sim_id in seen_simulation_ids:
                    rejected += 1
                    continue
                seen_simulation_ids.add(sim_id)

            row = validate_feedback_record(ev_data, act_data, case.amount)
            if row is None:
                rejected += 1
                continue
            rows.append(row)

        if not rows:
            return pd.DataFrame(columns=ALL_FEATURES + [TARGET_COLUMN]), rejected

        df = pd.DataFrame(rows)
        leak_cols = [c for c in df.columns if c in LEAKAGE_FIELDS or c in DECISION_CONTEXT_FIELDS]
        if leak_cols:
            df = df.drop(columns=leak_cols)
        return df[ALL_FEATURES + [TARGET_COLUMN]], rejected

    def extract_feedback_dataframe(self, db: Session) -> pd.DataFrame:
        """Extract clean feedback records: 12 Group A features + recovered label only."""
        df, _rejected = self.extract_feedback_dataset(db)
        return df


learning_service = LearningService()
