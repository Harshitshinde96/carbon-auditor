from app.core.exceptions import (
    CarbonBaseException,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    ValidationProcessingError,
    OCRProcessingError,
    InvalidConsumptionError,
    UnsupportedUtilityTypeError,
    UnitMismatchError,
)


def test_base_exception():
    exc = CarbonBaseException(
        status_code=418, message="I'm a teapot", details=["Short and stout"]
    )
    assert exc.status_code == 418
    assert exc.message == "I'm a teapot"
    assert exc.details == ["Short and stout"]


def test_authentication_error():
    exc = AuthenticationError("Invalid token")
    assert exc.status_code == 401
    assert exc.message == "Invalid token"


def test_authorization_error():
    exc = AuthorizationError("Not allowed")
    assert exc.status_code == 403
    assert exc.message == "Not allowed"


def test_resource_not_found_error():
    exc = ResourceNotFoundError("User not found")
    assert exc.status_code == 404
    assert exc.message == "User not found"


def test_validation_processing_error():
    exc = ValidationProcessingError("Bad data", details=["Field X is required"])
    assert exc.status_code == 422
    assert exc.message == "Bad data"
    assert exc.details == ["Field X is required"]


def test_ocr_processing_error():
    exc = OCRProcessingError("Failed to read image")
    assert exc.status_code == 500
    assert exc.message == "Failed to read image"


def test_calc_engine_errors():
    exc1 = InvalidConsumptionError("Consumption cannot be negative")
    assert exc1.status_code == 400
    assert exc1.message == "Consumption cannot be negative"

    exc2 = UnsupportedUtilityTypeError("Wood is not supported")
    assert exc2.status_code == 400
    assert exc2.message == "Wood is not supported"

    exc3 = UnitMismatchError("Expected kWh, got Gallons")
    assert exc3.status_code == 400
    assert exc3.message == "Expected kWh, got Gallons"
