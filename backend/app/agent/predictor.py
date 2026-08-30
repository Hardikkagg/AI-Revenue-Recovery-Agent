"""Supervised ML predictor service for recovery probability scoring."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline

from app.agent.schemas import DetectedEvent

logger = logging.getLogger(__name__)

NUMERICAL_FEATURES = [
    "amount",
    "customer_age",
    "account_age",
    "previous_successes",
    "previous_failures",
    "retry_count",
    "checkout_visits",
    "cart_value",
    "subscription_age",
]

CATEGORICAL_FEATURES = [
    "event_type",
    "payment_method",
    "failure_reason",
]

DEFAULT_SEARCH_PATHS = [
    Path(os.getenv("RECOVERY_MODEL_PATH", "")) if os.getenv("RECOVERY_MODEL_PATH") else None,
    Path(__file__).resolve().parent.parent.parent / "models" / "recovery_model.joblib",
    Path(__file__).resolve().parent.parent.parent.parent / "models" / "recovery_model.joblib",
]


class MLPredictor:
    """Loads and runs inference using the trained scikit-learn recovery model."""

    def __init__(self, model_path: Path | str | None = None) -> None:
        self._model: Pipeline | None = None
        self._model_path: Path | None = None
        self.load_model(model_path)

    def find_model_file(self, explicit_path: Path | str | None = None) -> Path | None:
        if explicit_path is not None:
            p = Path(explicit_path)
            if p.exists() and p.is_file():
                return p
            return None

        for candidate in DEFAULT_SEARCH_PATHS:
            if candidate and candidate.exists() and candidate.is_file():
                return candidate
        return None

    def load_model(self, model_path: Path | str | None = None) -> bool:
        """Load the model pipeline into memory."""
        target = self.find_model_file(model_path)
        if not target:
            logger.info("No ML recovery model found at standard paths. Fallback mode active.")
            self._model = None
            self._model_path = None
            return False

        try:
            loaded = joblib.load(target)
            if isinstance(loaded, Pipeline):
                self._model = loaded
                self._model_path = target
                logger.info(f"Loaded ML recovery model from {target}")
                return True
            else:
                logger.warning(f"File at {target} is not a valid Pipeline.")
                self._model = None
                return False
        except Exception as exc:
            logger.warning(f"Failed to load ML model from {target}: {exc}. Fallback mode active.")
            self._model = None
            return False

    @property
    def is_available(self) -> bool:
        return self._model is not None

    def _event_to_dataframe(self, event: DetectedEvent) -> pd.DataFrame:
        row: dict[str, Any] = {
            "amount": float(event.amount),
            "customer_age": float(event.customer_age) if event.customer_age is not None else 35.0,
            "account_age": int(event.account_age),
            "previous_successes": int(event.previous_successes),
            "previous_failures": int(event.previous_failures),
            "retry_count": int(event.retry_count),
            "checkout_visits": int(event.checkout_visits),
            "cart_value": float(event.cart_value),
            "subscription_age": int(event.subscription_age),
            "event_type": str(event.event_type),
            "payment_method": str(event.payment_method),
            "failure_reason": str(event.failure_reason),
        }
        return pd.DataFrame([row])[NUMERICAL_FEATURES + CATEGORICAL_FEATURES]

    def _explain_prediction(self, df: pd.DataFrame) -> list[str]:
        """Extract top feature contributions from LogisticRegression weights."""
        if not self._model:
            return []

        try:
            preprocessor = self._model.named_steps.get("preprocessor")
            classifier = self._model.named_steps.get("classifier")

            if not preprocessor or not classifier:
                return []

            feature_names = preprocessor.get_feature_names_out()
            X_trans = preprocessor.transform(df)
            coefs = classifier.coef_[0]

            contributions = []
            for name, val, w in zip(feature_names, X_trans[0], coefs):
                if val != 0:
                    contrib = float(w * val)
                    clean_name = name.replace("num__", "").replace("cat__", "")
                    contributions.append((clean_name, contrib))

            # Sort by absolute impact
            contributions.sort(key=lambda item: abs(item[1]), reverse=True)
            top_factors = [
                f"{name}={'+' if c > 0 else ''}{c:.3f}"
                for name, c in contributions[:5]
            ]
            return top_factors
        except Exception:
            return []

    def predict(self, event: DetectedEvent) -> tuple[float, list[str]] | None:
        """Return (probability, factors) or None if unavailable."""
        if not self._model:
            return None

        try:
            df = self._event_to_dataframe(event)
            prob = float(self._model.predict_proba(df)[0, 1])
            factors = self._explain_prediction(df)
            return round(max(0.0, min(1.0, prob)), 4), factors
        except Exception as exc:
            logger.warning(f"ML prediction failed: {exc}. Using fallback.")
            return None


# Global singleton instance
ml_predictor = MLPredictor()
