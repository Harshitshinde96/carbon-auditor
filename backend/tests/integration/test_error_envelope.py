from fastapi.testclient import TestClient
from app.core.exceptions import (
    AuthenticationError,
    ValidationProcessingError,
    OCRProcessingError,
)

# Note: We need a temporary route in the app to raise these for testing.
# We will inject it into the app in the test file, or the app can have a test router.
# Let's inject it into the app dynamically.

from main import app


@app.get("/_test_error/401")
def raise_401():
    raise AuthenticationError(message="Invalid token", details=["Token expired"])


@app.get("/_test_error/422")
def raise_422():
    raise ValidationProcessingError(message="Bad data", details=["Field missing"])


@app.get("/_test_error/500")
def raise_500():
    raise OCRProcessingError(message="OCR failed")


client = TestClient(app)


def test_error_envelope_401():
    response = client.get("/_test_error/401")
    assert response.status_code == 401
    data = response.json()
    assert data["status"] == "error"
    assert data["code"] == 401
    assert data["message"] == "Invalid token"
    assert data["details"] == ["Token expired"]


def test_error_envelope_422():
    response = client.get("/_test_error/422")
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert data["code"] == 422
    assert data["message"] == "Bad data"
    assert data["details"] == ["Field missing"]


def test_error_envelope_500():
    response = client.get("/_test_error/500")
    assert response.status_code == 500
    data = response.json()
    assert data["status"] == "error"
    assert data["code"] == 500
    assert data["message"] == "OCR failed"
    assert data["details"] == []


# Test default FastAPI validation error (RequestValidationError)
def test_fastapi_validation_error():
    # If we hit an endpoint that expects a query param but we don't provide it
    # We need an endpoint for this
    @app.get("/_test_error/validation")
    def raise_fastapi_422(item_id: int):
        return {"item_id": item_id}

    response = client.get("/_test_error/validation?item_id=not-an-int")
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert data["code"] == 422
    assert "message" in data
    assert "details" in data
