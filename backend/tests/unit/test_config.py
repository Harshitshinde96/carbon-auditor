import pytest
from pydantic import ValidationError
from app.core.config import Settings


def test_settings_load_from_env(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini")
    monkeypatch.setenv("QDRANT_API_KEY", "test-qdrant")
    monkeypatch.setenv("QDRANT_URL", "http://test-qdrant")
    monkeypatch.setenv("S3_UPLOAD_BUCKET", "test-bucket")
    monkeypatch.setenv("DYNAMO_TABLE_USERS", "test-users")
    monkeypatch.setenv("DYNAMO_TABLE_BILLS", "test-bills")
    monkeypatch.setenv("DYNAMO_TABLE_EMISSIONS", "test-emissions")
    monkeypatch.setenv("DYNAMO_TABLE_SETTINGS", "test-settings")
    monkeypatch.setenv("DYNAMO_TABLE_REPORTS", "test-reports")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    settings = Settings()
    assert settings.JWT_SECRET == "test-secret"
    assert settings.GEMINI_API_KEY == "test-gemini"
    assert settings.DYNAMO_TABLE_USERS == "test-users"
    assert settings.AWS_REGION == "us-east-1"


def test_settings_missing_required_env_var(monkeypatch):
    # Clear environment variables to ensure it's empty for this test
    monkeypatch.delenv("JWT_SECRET", raising=False)

    with pytest.raises(ValidationError):
        # Override env_file to None so it doesn't read from .env
        Settings(_env_file=None)
