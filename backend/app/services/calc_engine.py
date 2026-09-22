from app.core.exceptions import (
    InvalidConsumptionError,
    UnsupportedUtilityTypeError,
    UnitMismatchError,
)


def calculate_emissions(utility_type: str, consumption: float, unit: str) -> float:
    """
    Calculates CO2e emissions deterministically based on GHG Protocol factors.
    Returns the emissions in kg CO2e, rounded to 2 decimal places.
    """
    if consumption < 0:
        raise InvalidConsumptionError("Consumption cannot be negative")

    utility_type_lower = utility_type.strip().lower()

    # Define exact supported units and emission factors per PRD §13
    if utility_type_lower == "electricity":
        if unit.strip().lower() != "kwh":
            raise UnitMismatchError(f"Expected kWh for Electricity, got {unit}")
        # 0.385 kg CO2e / kWh
        emissions = consumption * 0.385

    elif utility_type_lower == "natural gas":
        if unit.strip().lower() != "therms":
            raise UnitMismatchError(f"Expected Therms for Natural Gas, got {unit}")
        # 5.3 kg CO2e / Therm
        emissions = consumption * 5.3

    elif utility_type_lower == "water":
        if unit.strip().lower() != "gallons":
            raise UnitMismatchError(f"Expected Gallons for Water, got {unit}")
        # 0.344 kg CO2e / 1000 Gallons
        emissions = (consumption / 1000.0) * 0.344

    else:
        raise UnsupportedUtilityTypeError(f"Unsupported utility type: {utility_type}")

    # PRD §28.4 requires rounding to 2 decimal places at calculation time
    return round(emissions, 2)
