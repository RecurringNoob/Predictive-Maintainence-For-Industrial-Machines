from __future__ import annotations

import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

MACHINE_TYPE_MAP = {"L": 0, "M": 1, "H": 2}

FAILURE_LABELS = [
    "No Failure",
    "Heat Dissipation Failure",
    "Power Failure",
    "Overstrain Failure",
    "Tool Wear Failure",
    "Random Failures",
]

NUMERIC_FEATURE_NAMES = [
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
]

ALL_FEATURE_NAMES = ["Type", *NUMERIC_FEATURE_NAMES]


class MLService:
    """Single source of truth for all ML inference."""

    def __init__(self, model_path: str, scaler_path: str) -> None:
        self.model_path = model_path
        self.scaler_path = scaler_path
        self._model = None
        self._scaler = None
        self._load()

    def _load(self) -> None:
        model_file = Path(self.model_path)
        scaler_file = Path(self.scaler_path)

        if not model_file.exists():
            raise FileNotFoundError(f"Model file not found: {model_file.resolve()}")
        if not scaler_file.exists():
            raise FileNotFoundError(f"Scaler file not found: {scaler_file.resolve()}")

        self._model = joblib.load(model_file)
        self._scaler = joblib.load(scaler_file)
        logger.info("ML model and scaler loaded successfully.")

    def predict(
        self,
        machine_type: str,
        air_temp_k: float,
        process_temp_k: float,
        rotational_speed_rpm: float,
        torque_nm: float,
        tool_wear_min: float,
    ) -> dict:
        """
        Run inference on a single set of sensor readings.

        Returns a dict with:
          - failure_type: str
          - confidence: float (0–1)
          - assumed_features: list[str]  — features that used defaults
        """
        assumed: list[str] = []

        # Encode machine type
        type_encoded = MACHINE_TYPE_MAP.get(machine_type.upper(), 1)

        # Build named DataFrame so scaler doesn't warn about feature names
        numeric = pd.DataFrame(
            [[air_temp_k, process_temp_k, rotational_speed_rpm, torque_nm, tool_wear_min]],
            columns=NUMERIC_FEATURE_NAMES,
        )
        scaled = self._scaler.transform(numeric)

        # Concatenate type + scaled features into a named DataFrame
        # Column order must match training: Type first, then the 5 numeric
        features = pd.DataFrame(
            [[type_encoded, *scaled[0]]],
            columns=ALL_FEATURE_NAMES,
        )

        prediction = self._model.predict(features)[0]
        probabilities = self._model.predict_proba(features)[0]
        confidence = float(probabilities.max())

        # Map prediction to label
        if isinstance(prediction, (int, np.integer)):
            failure_type = (
                FAILURE_LABELS[int(prediction)]
                if int(prediction) < len(FAILURE_LABELS)
                else str(prediction)
            )
        else:
            failure_type = str(prediction)

        return {
            "failure_type": failure_type,
            "confidence": round(confidence, 4),
            "assumed_features": assumed,
        }


_ml_service: MLService | None = None


def get_ml_service() -> MLService:
    """Return the singleton MLService instance."""
    global _ml_service
    if _ml_service is None:
        raise RuntimeError(
            "MLService has not been initialised. "
            "Call init_ml_service() during app startup."
        )
    return _ml_service


def init_ml_service(model_path: str, scaler_path: str) -> MLService:
    """Initialise and cache the singleton MLService. Call once at startup."""
    global _ml_service
    _ml_service = MLService(model_path=model_path, scaler_path=scaler_path)
    return _ml_service