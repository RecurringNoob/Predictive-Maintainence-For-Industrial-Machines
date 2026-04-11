"""
Unit tests for MLService.

These tests use stub model/scaler objects so they run without the real .pkl files.
They verify the preprocessing pipeline is correct — i.e. Type is encoded but NOT scaled,
and the 5 numeric features ARE scaled before being passed to model.predict().
"""

import pickle
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from schemas.sensor import SensorReadingCreate


def make_stub_pkl(tmp_path):
    stub_model = MagicMock()
    stub_model.predict.return_value = np.array(["No Failure"])
    stub_model.predict_proba.return_value = np.array([[0.9, 0.02, 0.02, 0.02, 0.02, 0.02]])

    stub_scaler = MagicMock()
    # Return a fixed scaled array so we can assert exact values
    stub_scaler.transform.return_value = np.array([[1.0, 2.0, 3.0, 4.0, 5.0]])

    model_path = tmp_path / "model.pkl"
    scaler_path = tmp_path / "scaler.pkl"

    with open(model_path, "wb") as f:
        pickle.dump(stub_model, f)
    with open(scaler_path, "wb") as f:
        pickle.dump(stub_scaler, f)

    return stub_model, stub_scaler, str(model_path), str(scaler_path)


@pytest.fixture
def ml(tmp_path):
    stub_model, stub_scaler, model_path, scaler_path = make_stub_pkl(tmp_path)
    settings_mock = MagicMock()
    settings_mock.model_path = model_path
    settings_mock.scaler_path = scaler_path
    settings_mock.model_version = "test-v1"

    with patch("services.ml_service.get_settings", return_value=settings_mock):
        from services.ml_service import MLService
        service = MLService()
        # Expose stubs for assertion
        service._stub_model = stub_model
        service._stub_scaler = stub_scaler
        return service


def make_reading(**kwargs) -> SensorReadingCreate:
    defaults = dict(
        machine_type="M",
        air_temp_k=300.0,
        process_temp_k=310.0,
        rpm=1500.0,
        torque_nm=40.0,
        tool_wear_min=100.0,
        source="manual",
    )
    defaults.update(kwargs)
    return SensorReadingCreate(**defaults)


class TestMLServicePreprocessing:
    def test_type_encoding_L(self, ml):
        ml.predict(make_reading(machine_type="L"))
        X = ml._stub_model.predict.call_args[0][0]
        assert X[0, 0] == 0, "L should encode to 0"

    def test_type_encoding_M(self, ml):
        ml.predict(make_reading(machine_type="M"))
        X = ml._stub_model.predict.call_args[0][0]
        assert X[0, 0] == 1, "M should encode to 1"

    def test_type_encoding_H(self, ml):
        ml.predict(make_reading(machine_type="H"))
        X = ml._stub_model.predict.call_args[0][0]
        assert X[0, 0] == 2, "H should encode to 2"

    def test_scaler_receives_5_numeric_features(self, ml):
        reading = make_reading(
            air_temp_k=300.0,
            process_temp_k=310.0,
            rpm=1500.0,
            torque_nm=40.0,
            tool_wear_min=100.0,
        )
        ml.predict(reading)
        call_args = ml._stub_scaler.transform.call_args[0][0]
        assert call_args.shape == (1, 5), "Scaler must receive exactly 5 numeric features"
        np.testing.assert_array_equal(
            call_args[0],
            [300.0, 310.0, 1500.0, 40.0, 100.0],
        )

    def test_type_column_not_scaled(self, ml):
        """Type value must come from encoding, NOT from scaler output."""
        ml.predict(make_reading(machine_type="H"))
        X = ml._stub_model.predict.call_args[0][0]
        # Scaler stub returns [1,2,3,4,5]; Type=H encodes to 2
        # Final X must be [2, 1, 2, 3, 4, 5] — not [1, 2, 3, 4, 5] with type lost
        assert X[0, 0] == 2
        np.testing.assert_array_equal(X[0, 1:], [1.0, 2.0, 3.0, 4.0, 5.0])

    def test_final_input_shape(self, ml):
        ml.predict(make_reading())
        X = ml._stub_model.predict.call_args[0][0]
        assert X.shape == (1, 6), "Model input must be shape (1, 6)"

    def test_returns_prediction_result(self, ml):
        result = ml.predict(make_reading())
        assert result.failure_type == "No Failure"
        assert 0.0 <= result.confidence <= 1.0
        assert result.model_version == "test-v1"

    def test_confidence_is_max_proba(self, ml):
        result = ml.predict(make_reading())
        # predict_proba stub returns [[0.9, 0.02, ...]] — max is 0.9
        assert abs(result.confidence - 0.9) < 1e-6


class TestMLServiceInit:
    def test_raises_if_model_missing(self, tmp_path):
        settings_mock = MagicMock()
        settings_mock.model_path = str(tmp_path / "nonexistent.pkl")
        settings_mock.scaler_path = str(tmp_path / "nonexistent_scaler.pkl")
        settings_mock.model_version = "v1"

        with patch("services.ml_service.get_settings", return_value=settings_mock):
            from services.ml_service import MLService
            with pytest.raises(FileNotFoundError, match="Model not found"):
                MLService()