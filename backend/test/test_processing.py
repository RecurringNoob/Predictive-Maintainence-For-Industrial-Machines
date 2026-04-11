"""
Tests for Pydantic schema validation — boundary conditions and business rules.
These run with no DB or model; pure Python.
"""

import pytest
from pydantic import ValidationError

from schemas.sensor import SensorReadingCreate


class TestSensorReadingCreate:
    def _valid(self, **overrides) -> dict:
        base = dict(
            machine_type="M",
            air_temp_k=300.0,
            process_temp_k=310.0,
            rpm=1500.0,
            torque_nm=40.0,
            tool_wear_min=100.0,
            source="manual",
        )
        base.update(overrides)
        return base

    def test_valid_passes(self):
        SensorReadingCreate(**self._valid())

    # machine_type
    @pytest.mark.parametrize("t", ["L", "M", "H"])
    def test_valid_machine_types(self, t):
        SensorReadingCreate(**self._valid(machine_type=t))

    def test_invalid_machine_type(self):
        with pytest.raises(ValidationError):
            SensorReadingCreate(**self._valid(machine_type="X"))

    # air_temp_k bounds
    def test_air_temp_too_low(self):
        with pytest.raises(ValidationError):
            SensorReadingCreate(**self._valid(air_temp_k=100.0))

    def test_air_temp_too_high(self):
        with pytest.raises(ValidationError):
            SensorReadingCreate(**self._valid(air_temp_k=600.0))

    # process_temp_k must be >= air_temp_k
    def test_process_temp_below_air_temp_fails(self):
        with pytest.raises(ValidationError, match="process_temp_k must be"):
            SensorReadingCreate(**self._valid(air_temp_k=310.0, process_temp_k=300.0))

    def test_process_temp_equal_to_air_temp_passes(self):
        SensorReadingCreate(**self._valid(air_temp_k=300.0, process_temp_k=300.0))

    # rpm bounds
    def test_rpm_zero_fails(self):
        with pytest.raises(ValidationError):
            SensorReadingCreate(**self._valid(rpm=0.0))

    def test_rpm_max_fails(self):
        with pytest.raises(ValidationError):
            SensorReadingCreate(**self._valid(rpm=6000.0))

    # torque_nm bounds
    def test_torque_negative_fails(self):
        with pytest.raises(ValidationError):
            SensorReadingCreate(**self._valid(torque_nm=-1.0))

    def test_torque_max_fails(self):
        with pytest.raises(ValidationError):
            SensorReadingCreate(**self._valid(torque_nm=250.0))

    # tool_wear_min bounds
    def test_wear_negative_fails(self):
        with pytest.raises(ValidationError):
            SensorReadingCreate(**self._valid(tool_wear_min=-1.0))

    def test_wear_max_fails(self):
        with pytest.raises(ValidationError):
            SensorReadingCreate(**self._valid(tool_wear_min=350.0))

    # source
    @pytest.mark.parametrize("s", ["iot", "manual"])
    def test_valid_sources(self, s):
        SensorReadingCreate(**self._valid(source=s))

    def test_invalid_source(self):
        with pytest.raises(ValidationError):
            SensorReadingCreate(**self._valid(source="kafka"))