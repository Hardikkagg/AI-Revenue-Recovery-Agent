"""Small contextual strategy policy for adaptive learning."""

from __future__ import annotations

import json
import math
import random
from collections.abc import Mapping
from typing import Any

DEFAULT_CONTEXT_FIELDS = (
    "event_type",
    "diagnosis_code",
    "payment_method",
    "probability_bucket",
    "retry_bucket",
)
POST_OUTCOME_FIELDS = {
    "recovered",
    "recovered_amount",
    "outcome",
    "reward",
    "status",
    "simulation_id",
    "gateway_reference",
    "customer_responded",
    "action_details",
    "explanation",
    "result",
    "selected_strategy",
}


class AdaptiveStrategyPolicy:
    """Simple epsilon-greedy contextual policy over allowed strategies."""

    def __init__(self, epsilon: float = 0.15, seed: int | None = None, min_samples: int = 1) -> None:
        self.epsilon = max(0.0, min(1.0, float(epsilon)))
        self.min_samples = max(1, int(min_samples))
        self.rng = random.Random(seed)
        self._stats: dict[str, dict[str, dict[str, float]]] = {}

    def build_context_key(self, context: Mapping[str, Any] | None) -> str:
        """Build a compact decision-time context key using safe pre-execution attributes only."""
        if not context:
            return "__empty__"

        cleaned: dict[str, str] = {}
        for key in DEFAULT_CONTEXT_FIELDS:
            if key in context and context[key] is not None:
                cleaned[key] = str(context[key]).strip().lower()

        for key, value in context.items():
            if key in POST_OUTCOME_FIELDS:
                continue
            if key.startswith("recovered") or key.startswith("outcome"):
                continue
            if key not in DEFAULT_CONTEXT_FIELDS and key not in cleaned:
                cleaned[key] = str(value).strip().lower()

        return json.dumps(cleaned, sort_keys=True)

    def update_from_feedback(self, context: Mapping[str, Any], strategy: str, reward: float) -> None:
        """Update strategy reward statistics for a context."""
        if not strategy:
            return
        try:
            reward_value = float(reward)
        except (TypeError, ValueError):
            return
        if math.isnan(reward_value):
            return

        key = self.build_context_key(context)
        bucket = self._stats.setdefault(key, {})
        stats = bucket.setdefault(strategy, {"count": 0.0, "total_reward": 0.0})
        stats["count"] += 1.0
        stats["total_reward"] += reward_value

    def get_strategy_reward(self, context: Mapping[str, Any], strategy: str) -> float:
        """Return average historical reward for one strategy in this context."""
        key = self.build_context_key(context)
        bucket = self._stats.get(key, {})
        stats = bucket.get(strategy)
        if not stats or stats.get("count", 0.0) <= 0:
            return 0.0
        return float(stats["total_reward"]) / float(stats["count"])

    def select_strategy(
        self,
        context: Mapping[str, Any],
        allowed_strategies: list[str],
        deterministic_strategy: str,
    ) -> str:
        """Choose a strategy from allowed strategies using epsilon-greedy logic."""
        safe_allowed = [s for s in allowed_strategies if isinstance(s, str) and s]
        if not safe_allowed:
            return deterministic_strategy

        if deterministic_strategy not in safe_allowed:
            deterministic_strategy = safe_allowed[0]

        context_key = self.build_context_key(context)
        stats = self._stats.get(context_key, {})
        usable = [
            s for s in safe_allowed if stats.get(s, {}).get("count", 0.0) >= float(self.min_samples)
        ]

        if not usable:
            return deterministic_strategy

        if self.rng.random() < self.epsilon:
            return self.rng.choice(safe_allowed)

        best_strategy = max(
            safe_allowed,
            key=lambda strategy: (self.get_strategy_reward(context, strategy), strategy),
        )
        return best_strategy if best_strategy in safe_allowed else deterministic_strategy

    def load_from_feedback(self, records: list[dict[str, Any]]) -> None:
        """Load historical records into the policy."""
        for record in records:
            if not isinstance(record, dict):
                continue
            strategy = record.get("strategy")
            reward = record.get("reward")
            if not strategy:
                continue
            context = {
                "event_type": record.get("event_type"),
                "diagnosis_code": record.get("diagnosis_code"),
                "payment_method": record.get("payment_method"),
                "probability_bucket": record.get("probability_bucket"),
                "retry_bucket": record.get("retry_bucket"),
            }
            self.update_from_feedback(context, str(strategy), reward)


adaptive_policy = AdaptiveStrategyPolicy(seed=42, epsilon=0.15)
