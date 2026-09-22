import pytest
from app.services.calc_engine import calculate_emissions
from app.core.exceptions import (
    InvalidConsumptionError,
    UnsupportedUtilityTypeError,
    UnitMismatchError,
)


def test_electricity_normal_consumption():
    # 100 kWh * 0.385 = 38.5
    emissions = calculate_emissions("Electricity", 100.0, "kWh")
    assert emissions == 38.5


def test_natural_gas_normal_consumption():
    # 10 Therms * 5.3 = 53.0
    emissions = calculate_emissions("Natural Gas", 10.0, "Therms")
    assert emissions == 53.0


def test_water_normal_consumption():
    # 2000 Gallons = 2 * 1000 Gallons * 0.344 = 0.688 -> rounds to 0.69
    emissions = calculate_emissions("Water", 2000.0, "Gallons")
    assert emissions == 0.69


def test_zero_consumption():
    assert calculate_emissions("Electricity", 0.0, "kWh") == 0.0


def test_negative_consumption():
    with pytest.raises(InvalidConsumptionError) as exc_info:
        calculate_emissions("Electricity", -10.0, "kWh")
    assert exc_info.value.status_code == 400


def test_unsupported_utility_type():
    with pytest.raises(UnsupportedUtilityTypeError) as exc_info:
        calculate_emissions("Wood", 100.0, "kg")
    assert exc_info.value.status_code == 400


def test_unit_mismatch():
    with pytest.raises(UnitMismatchError) as exc_info:
        calculate_emissions("Electricity", 100.0, "Gallons")
    assert exc_info.value.status_code == 400

    with pytest.raises(UnitMismatchError) as exc_info2:
        calculate_emissions("Natural Gas", 10.0, "kWh")
    assert exc_info2.value.status_code == 400

    with pytest.raises(UnitMismatchError) as exc_info3:
        calculate_emissions("Water", 1000.0, "Therms")
    assert exc_info3.value.status_code == 400


def test_rounding_rule():
    # 1000.123 kWh * 0.385 = 385.047355 -> 385.05
    emissions = calculate_emissions("Electricity", 1000.123, "kWh")
    assert emissions == 385.05
