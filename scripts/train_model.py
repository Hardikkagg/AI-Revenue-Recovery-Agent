"""Train supervised ML recovery probability model from historical dataset."""

from __future__ import annotations

import argparse
import json
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
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "historical_events.csv"
DEFAULT_MODEL_PATH = PROJECT_ROOT / "backend" / "models" / "recovery_model.joblib"
DEFAULT_METRICS_PATH = PROJECT_ROOT / "backend" / "models" / "model_metrics.json"

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

TARGET_COLUMN = "recovered"


def load_dataset(csv_path: Path | str) -> pd.DataFrame:
    """Load historical events dataset."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Historical dataset not found at {path}")
    return pd.read_csv(path)


def build_pipeline() -> Pipeline:
    """Construct preprocessing + LogisticRegression pipeline."""
    num_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    cat_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="unknown")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_transformer, NUMERICAL_FEATURES),
            ("cat", cat_transformer, CATEGORICAL_FEATURES),
        ]
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                LogisticRegression(
                    C=1.0,
                    max_iter=1000,
                    random_state=42,
                ),
            ),
        ]
    )
    return pipeline


def train_model(
    data_path: Path | str = DEFAULT_DATA_PATH,
    model_output_path: Path | str = DEFAULT_MODEL_PATH,
    metrics_output_path: Path | str = DEFAULT_METRICS_PATH,
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict[str, Any]:
    """Train, evaluate via holdout and cross-validation, and save the recovery probability model."""
    df = load_dataset(data_path)

    features = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
    X = df[features]
    y = df[TARGET_COLUMN].astype(int)

    class_dist = y.value_counts(normalize=True).to_dict()
    total_samples = len(df)

    # 1. 5-Fold Stratified Cross-Validation on Full Dataset
    pipeline_cv = build_pipeline()
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    cv_results = cross_validate(
        pipeline_cv,
        X,
        y,
        cv=skf,
        scoring=["accuracy", "precision", "recall", "f1", "roc_auc"],
        return_train_score=True,
    )

    # 2. Stratified 80/20 Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    train_pred = pipeline.predict(X_train)
    train_prob = pipeline.predict_proba(X_train)[:, 1]
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    train_acc = float(accuracy_score(y_train, train_pred))
    train_auc = float(roc_auc_score(y_train, train_prob))

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    auc = float(roc_auc_score(y_test, y_prob))
    cm = confusion_matrix(y_test, y_pred).tolist()
    report_dict = classification_report(y_test, y_pred, output_dict=True)

    metrics = {
        "model_type": "LogisticRegression",
        "dataset_size": total_samples,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "class_distribution": {str(k): float(v) for k, v in class_dist.items()},
        "features": {
            "numerical": NUMERICAL_FEATURES,
            "categorical": CATEGORICAL_FEATURES,
        },
        "target": TARGET_COLUMN,
        "holdout_metrics": {
            "train_accuracy": round(train_acc, 4),
            "train_roc_auc": round(train_auc, 4),
            "test_accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(auc, 4),
            "confusion_matrix": cm,
        },
        "cross_validation_5fold": {
            "cv_accuracy_mean": round(float(np.mean(cv_results["test_accuracy"])), 4),
            "cv_accuracy_std": round(float(np.std(cv_results["test_accuracy"])), 4),
            "cv_f1_mean": round(float(np.mean(cv_results["test_f1"])), 4),
            "cv_f1_std": round(float(np.std(cv_results["test_f1"])), 4),
            "cv_roc_auc_mean": round(float(np.mean(cv_results["test_roc_auc"])), 4),
            "cv_roc_auc_std": round(float(np.std(cv_results["test_roc_auc"])), 4),
        },
        "classification_report": report_dict,
    }

    # Save serialized model artifact
    out_path = Path(model_output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, out_path)

    # Save metrics JSON
    if metrics_output_path:
        met_path = Path(metrics_output_path)
        met_path.parent.mkdir(parents=True, exist_ok=True)
        with open(met_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)

    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train ML recovery probability model.")
    parser.add_argument("--data", type=str, default=str(DEFAULT_DATA_PATH), help="Path to CSV dataset")
    parser.add_argument("--output", type=str, default=str(DEFAULT_MODEL_PATH), help="Output path for joblib model")
    parser.add_argument("--metrics", type=str, default=str(DEFAULT_METRICS_PATH), help="Output path for metrics JSON")
    args = parser.parse_args()

    print(f"Training recovery model from {args.data}...")
    metrics = train_model(data_path=args.data, model_output_path=args.output, metrics_output_path=args.metrics)
    print("\n--- Training Results (Holdout) ---")
    print(f"Model: {metrics['model_type']}")
    print(f"Dataset: {metrics['dataset_size']} rows (Train: {metrics['train_samples']}, Test: {metrics['test_samples']})")
    print(f"Train Accuracy:  {metrics['holdout_metrics']['train_accuracy']:.4f}")
    print(f"Test Accuracy:   {metrics['holdout_metrics']['test_accuracy']:.4f}")
    print(f"Precision:       {metrics['holdout_metrics']['precision']:.4f}")
    print(f"Recall:          {metrics['holdout_metrics']['recall']:.4f}")
    print(f"F1 Score:        {metrics['holdout_metrics']['f1_score']:.4f}")
    print(f"ROC-AUC:         {metrics['holdout_metrics']['roc_auc']:.4f}")
    print(f"Confusion Matrix: {metrics['holdout_metrics']['confusion_matrix']}")
    print("\n--- 5-Fold Stratified Cross-Validation ---")
    print(f"CV Accuracy: {metrics['cross_validation_5fold']['cv_accuracy_mean']:.4f} +/- {metrics['cross_validation_5fold']['cv_accuracy_std']:.4f}")
    print(f"CV F1 Score: {metrics['cross_validation_5fold']['cv_f1_mean']:.4f} +/- {metrics['cross_validation_5fold']['cv_f1_std']:.4f}")
    print(f"CV ROC-AUC:  {metrics['cross_validation_5fold']['cv_roc_auc_mean']:.4f} +/- {metrics['cross_validation_5fold']['cv_roc_auc_std']:.4f}")
    print(f"\nModel saved to: {args.output}")


if __name__ == "__main__":
    main()
