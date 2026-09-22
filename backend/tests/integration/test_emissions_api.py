import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_emissions_repo():
    with patch("app.api.v1.emissions.DynamoRepository") as mock:
        yield mock


def test_get_emissions_summary_empty(mock_emissions_repo):
    mock_repo_instance = mock_emissions_repo.return_value
    mock_repo_instance.query.return_value = ([], None)

    response = client.get("/api/v1/emissions/summary")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_co2e_kg"] == 0
    assert data["breakdown"] == {"SCOPE_1": 0, "SCOPE_2": 0, "SCOPE_3": 0}


def test_get_emissions_summary_with_data(mock_emissions_repo):
    mock_repo_instance = mock_emissions_repo.return_value

    mock_repo_instance.query.return_value = (
        [
            {"scope": "SCOPE_1", "co2e_kg": 10},
            {"scope": "SCOPE_2", "co2e_kg": 20},
            {"scope": "SCOPE_3", "co2e_kg": 10},
        ],
        None,
    )

    response = client.get("/api/v1/emissions/summary")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_co2e_kg"] == 40
    assert data["breakdown"] == {"SCOPE_1": 10.0, "SCOPE_2": 20.0, "SCOPE_3": 10.0}
