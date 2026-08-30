"""Model Retrainer: trains a candidate from feedback and promotes it only if validation passes."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sqlalchemy.orm import Session

from app.agent.predictor import CATEGORICAL_FEATURES, NUMERICAL_FEATURES, ml_predictor
from app.learning.schemas import RetrainResponse
from app.learning.service import learning_service

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "historical_events.csv"
DEFAULT_MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "models" / "recovery_model.joblib"
DEFAULT_METRICS_PATH = Path(__file__).resolve().parent.parent.parent / "models" / "model_metrics.json"
DEFAULT_CANDIDATE_MODEL_PATH = (
    Path(__file__).resolve().parent.parent.parent / "models" / "candidate_recovery_model.joblib"
)

ALL_FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
TARGET_COLUMN = "recovered"
MIN_ROC_AUC = 0.52
MAX_ROC_AUC_DROP = 0.05
MAX_ACCURACY_DROP = 0.05


def _build_training_pipeline() -> Pipeline:
    num_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    cat_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="unknown")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_transformer, NUMERICAL_FEATURES),
            ("cat", cat_transformer, CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(C=1.0, max_iter=1000, random_state=42)),
        ]
    )


def _load_current_metrics(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return {}


def _should_promote(candidate_holdout: dict[str, Any], current_holdout: dict[str, Any]) -> tuple[bool, str]:
    candidate_auc = float(candidate_holdout.get("roc_auc", 0.0))
    candidate_acc = float(candidate_holdout.get("test_accuracy", 0.0))

    if candidate_auc < MIN_ROC_AUC:
        return False, (
            f"Candidate ROC-AUC {candidate_auc:.4f} is below the minimum {MIN_ROC_AUC:.2f}. "
            "Current production model retained."
        )

    current_auc = current_holdout.get("roc_auc")
    current_acc = current_holdout.get("test_accuracy")
    if current_auc is not None and candidate_auc < float(current_auc) - MAX_ROC_AUC_DROP:
        return False, (
            f"Candidate ROC-AUC {candidate_auc:.4f} dropped more than {MAX_ROC_AUC_DROP:.2f} "
            f"from current {float(current_auc):.4f}. Current production model retained."
        )
    if current_acc is not None and candidate_acc < float(current_acc) - MAX_ACCURACY_DROP:
        return False, (
            f"Candidate accuracy {candidate_acc:.4f} dropped more than {MAX_ACCURACY_DROP:.2f} "
            f"from current {float(current_acc):.4f}. Current production model retained."
        )

    return True, (
        f"Candidate passed validation (ROC-AUC {candidate_auc:.4f}, "
        f"accuracy {candidate_acc:.4f}) and was promoted."
    )


class ModelRetrainer:
    """Combines historical baseline data with live simulation feedback and updates the ML predictor."""

    def retrain(
        self,
        db: Session,
        baseline_path: Path | str | None = None,
        model_output_path: Path | str | None = None,
        metrics_output_path: Path | str | None = None,
        candidate_model_path: Path | str | None = None,
        random_state: int = 42,
        force_reject: bool = False,
    ) -> RetrainResponse:
        """Train a candidate model; promote only if it passes validation against the current model."""
        baseline_path = Path(baseline_path) if baseline_path else DEFAULT_DATA_PATH
        model_output_path = Path(model_output_path) if model_output_path else DEFAULT_MODEL_PATH
        metrics_output_path = Path(metrics_output_path) if metrics_output_path else DEFAULT_METRICS_PATH
        baseline_df = pd.read_csv(baseline_path)
        baseline_count = len(baseline_df)

        feedback_df, rejected_count = learning_service.extract_feedback_dataset(db)
        feedback_count = len(feedback_df)

        leak_cols = [c for c in feedback_df.columns if c not in ALL_FEATURES + [TARGET_COLUMN]]
        if leak_cols:
            raise ValueError(f"Target leakage in feedback dataset: {leak_cols}")

        if feedback_count > 0:
            combined_df = pd.concat(
                [baseline_df[ALL_FEATURES + [TARGET_COLUMN]], feedback_df[ALL_FEATURES + [TARGET_COLUMN]]],
                ignore_index=True,
            )
        else:
            combined_df = baseline_df[ALL_FEATURES + [TARGET_COLUMN]]

        X = combined_df[ALL_FEATURES]
        y = combined_df[TARGET_COLUMN].astype(int)
        if y.nunique() < 2:
            current = _load_current_metrics(Path(metrics_output_path))
            return RetrainResponse(
                success=True,
                promoted=False,
                message="Candidate training skipped: target has fewer than two classes. Current model retained.",
                baseline_samples=baseline_count,
                live_feedback_samples=feedback_count,
                rejected_feedback_samples=rejected_count,
                total_training_samples=len(combined_df),
                holdout_metrics={},
                cross_validation_5fold={},
                current_holdout_metrics=current.get("holdout_metrics", {}),
            )

        pipeline_cv = _build_training_pipeline()
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
        cv_results = cross_validate(
            pipeline_cv,
            X,
            y,
            cv=skf,
            scoring=["accuracy", "precision", "recall", "f1", "roc_auc"],
            return_train_score=True,
        )

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=random_state,
            stratify=y,
        )

        pipeline = _build_training_pipeline()
        pipeline.fit(X_train, y_train)

        train_pred = pipeline.predict(X_train)
        train_prob = pipeline.predict_proba(X_train)[:, 1]
        y_pred = pipeline.predict(X_test)
        y_prob = pipeline.predict_proba(X_test)[:, 1]

        holdout_metrics = {
            "train_accuracy": round(float(accuracy_score(y_train, train_pred)), 4),
            "train_roc_auc": round(float(roc_auc_score(y_train, train_prob)), 4),
            "test_accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
            "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
            "f1_score": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
            "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        }
        cv_metrics = {
            "cv_accuracy_mean": round(float(np.mean(cv_results["test_accuracy"])), 4),
            "cv_accuracy_std": round(float(np.std(cv_results["test_accuracy"])), 4),
            "cv_f1_mean": round(float(np.mean(cv_results["test_f1"])), 4),
            "cv_f1_std": round(float(np.std(cv_results["test_f1"])), 4),
            "cv_roc_auc_mean": round(float(np.mean(cv_results["test_roc_auc"])), 4),
            "cv_roc_auc_std": round(float(np.std(cv_results["test_roc_auc"])), 4),
        }

        out_model_path = Path(model_output_path)
        candidate_path = Path(candidate_model_path) if candidate_model_path else DEFAULT_CANDIDATE_MODEL_PATH
        if candidate_path.resolve() == out_model_path.resolve():
            candidate_path = out_model_path.parent / "candidate_recovery_model.joblib"
        candidate_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(pipeline, candidate_path)

        current_metrics = _load_current_metrics(Path(metrics_output_path))
        current_holdout = current_metrics.get("holdout_metrics", {})
        promoted, reason = _should_promote(holdout_metrics, current_holdout)
        if force_reject:
            promoted = False
            reason = "Forced rejection for safety testing. Current production model retained."

        if promoted:
            out_model_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(candidate_path, out_model_path)
            production_metrics = {
                "model_type": "LogisticRegression",
                "dataset_size": len(combined_df),
                "baseline_samples": baseline_count,
                "feedback_samples": feedback_count,
                "rejected_feedback_samples": rejected_count,
                "promoted": True,
                "features": {"numerical": NUMERICAL_FEATURES, "categorical": CATEGORICAL_FEATURES},
                "target": TARGET_COLUMN,
                "holdout_metrics": holdout_metrics,
                "cross_validation_5fold": cv_metrics,
            }
            metrics_path = Path(metrics_output_path)
            metrics_path.parent.mkdir(parents=True, exist_ok=True)
            with metrics_path.open("w", encoding="utf-8") as handle:
                json.dump(production_metrics, handle, indent=2)
            ml_predictor.reload(out_model_path)

        return RetrainResponse(
            success=True,
            promoted=promoted,
            message=reason,
            baseline_samples=baseline_count,
            live_feedback_samples=feedback_count,
            rejected_feedback_samples=rejected_count,
            total_training_samples=len(combined_df),
            holdout_metrics=holdout_metrics,
            cross_validation_5fold=cv_metrics,
            current_holdout_metrics=current_holdout,
        )


model_retrainer = ModelRetrainer()
