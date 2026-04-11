"""
ml/train.py — Reproducible training pipeline for the RandomForest classifier.

Run from project root:
    python ml/train.py

Outputs:
    backend/ml/predictive_maintenance.pkl
    backend/ml/scaler.pkl
    ml/classification_report.txt
"""

import argparse
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.preprocessing import StandardScaler

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
DATA_PATH = ROOT / "ml" / "predictive_maintenance.csv"
MODEL_OUT = ROOT / "backend" / "ml" / "predictive_maintenance.pkl"
SCALER_OUT = ROOT / "backend" / "ml" / "scaler.pkl"
REPORT_OUT = ROOT / "ml" / "classification_report.txt"

# ── Column names ──────────────────────────────────────────────────────────────
TYPE_COL = "Type"
TARGET_COL = "Failure Type"
NUMERIC_COLS = [
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
]
DROP_COLS = ["UDI", "Product ID", "Target"]

TYPE_ENCODING = {"L": 0, "M": 1, "H": 2}

RANDOM_STATE = 42


def load_and_clean(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    print(f"Loaded {len(df):,} rows from {path.name}")
    df = df.drop(columns=[c for c in DROP_COLS if c in df.columns])
    df[TYPE_COL] = df[TYPE_COL].map(TYPE_ENCODING)
    if df[TYPE_COL].isna().any():
        raise ValueError("Unexpected values in 'Type' column after encoding")
    df = df.dropna()
    print(f"After cleaning: {len(df):,} rows")
    return df


def build_features(df: pd.DataFrame, scaler: StandardScaler | None = None):
    """
    Returns (X, y, fitted_scaler).
    If scaler is None, a new one is fitted on NUMERIC_COLS.
    Type column is NOT scaled — it keeps its ordinal integer value.
    """
    y = df[TARGET_COL].values

    numeric = df[NUMERIC_COLS].values
    if scaler is None:
        scaler = StandardScaler()
        numeric_scaled = scaler.fit_transform(numeric)
    else:
        numeric_scaled = scaler.transform(numeric)

    type_col = df[[TYPE_COL]].values  # shape (n, 1)
    X = np.hstack([type_col, numeric_scaled])
    return X, y, scaler


def train(data_path: Path = DATA_PATH) -> None:
    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)

    df = load_and_clean(data_path)

    # Train / test split — stratify on target to preserve class balance
    train_df, test_df = train_test_split(
        df, test_size=0.2, random_state=RANDOM_STATE, stratify=df[TARGET_COL]
    )

    X_train, y_train, scaler = build_features(train_df)
    X_test, y_test, _ = build_features(test_df, scaler=scaler)

    print(f"Train size: {len(X_train):,} | Test size: {len(X_test):,}")
    print(f"Class distribution (train):\n{pd.Series(y_train).value_counts()}\n")

    # ── Hyperparameter search ─────────────────────────────────────────────────
    param_grid = {
        "n_estimators": [100, 200],
        "max_depth": [None, 20, 40],
        "min_samples_split": [2, 5],
        "class_weight": ["balanced"],
    }

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    grid = GridSearchCV(
        RandomForestClassifier(random_state=RANDOM_STATE, n_jobs=-1),
        param_grid,
        cv=cv,
        scoring="f1_macro",
        n_jobs=-1,
        verbose=1,
        refit=True,
    )
    grid.fit(X_train, y_train)

    best = grid.best_estimator_
    print(f"\nBest params: {grid.best_params_}")
    print(f"Best CV F1-macro: {grid.best_score_:.4f}")

    # ── Evaluate on held-out test set ─────────────────────────────────────────
    y_pred = best.predict(X_test)
    report = classification_report(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred, labels=best.classes_)

    print("\n── Classification Report ─────────────────────────────")
    print(report)
    print("── Confusion Matrix ──────────────────────────────────")
    print(pd.DataFrame(cm, index=best.classes_, columns=best.classes_))

    REPORT_OUT.write_text(report)
    print(f"\nReport written to {REPORT_OUT}")

    # ── Persist artefacts ─────────────────────────────────────────────────────
    with open(MODEL_OUT, "wb") as f:
        pickle.dump(best, f, protocol=pickle.HIGHEST_PROTOCOL)
    with open(SCALER_OUT, "wb") as f:
        pickle.dump(scaler, f, protocol=pickle.HIGHEST_PROTOCOL)

    print(f"Model  → {MODEL_OUT}")
    print(f"Scaler → {SCALER_OUT}")
    print("Done ✓")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train predictive maintenance model")
    parser.add_argument(
        "--data",
        type=Path,
        default=DATA_PATH,
        help=f"Path to CSV (default: {DATA_PATH})",
    )
    args = parser.parse_args()
    train(data_path=args.data)