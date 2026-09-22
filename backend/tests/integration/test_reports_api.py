import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_repo():
    with patch("app.api.v1.reports.DynamoRepository") as mock:
        yield mock


@pytest.fixture
def mock_emissions_repo():
    with patch("app.api.v1.reports.get_emissions_repo") as mock:
        yield mock


def test_generate_report_valid(mock_repo, mock_emissions_repo):
    mock_repo_instance = mock_repo.return_value
    # Mock that no existing IN_PROGRESS report exists
    mock_repo_instance.query.return_value = ([], None)

    response = client.post(
        "/api/v1/reports/generate",
        headers={"Authorization": "Bearer token"},
        json={"period_start": "2023-01-01", "period_end": "2023-12-31"},
    )
    assert response.status_code == 202
    assert "report_id" in response.json()
    assert response.json()["status"] == "IN_PROGRESS"


def test_generate_report_invalid_range(mock_repo):
    response = client.post(
        "/api/v1/reports/generate",
        headers={"Authorization": "Bearer token"},
        json={"period_start": "2023-12-31", "period_end": "2023-01-01"},
    )
    assert response.status_code == 400


def test_generate_report_oversized_range(mock_repo):
    response = client.post(
        "/api/v1/reports/generate",
        headers={"Authorization": "Bearer token"},
        json={"period_start": "2022-01-01", "period_end": "2024-01-01"},
    )
    assert response.status_code == 400


def test_generate_report_concurrent(mock_repo):
    mock_repo_instance = mock_repo.return_value
    # Mock that an existing IN_PROGRESS report exists
    mock_repo_instance.query.return_value = ([{"status": "IN_PROGRESS"}], None)

    response = client.post(
        "/api/v1/reports/generate",
        headers={"Authorization": "Bearer token"},
        json={"period_start": "2023-01-01", "period_end": "2023-12-31"},
    )
    assert response.status_code == 409


def test_get_report(mock_repo):
    mock_repo_instance = mock_repo.return_value
    mock_repo_instance.get_item.return_value = {
        "report_id": "r1",
        "user_id": "user-1",
        "status": "COMPLETED",
        "pdf_url": "s3://some-url",
    }

    response = client.get(
        "/api/v1/reports/r1", headers={"Authorization": "Bearer token"}
    )
    assert response.status_code == 200
    assert response.json()["report_id"] == "r1"


@pytest.mark.asyncio
async def test_background_report_generation():
    from app.api.v1.reports import generate_report_background
    from app.services.report_service import validate_report_numbers

    # Mock repos
    mock_reports_repo = MagicMock()
    mock_emissions_repo = MagicMock()

    # Return some emissions
    mock_emissions_repo.query.return_value = (
        [{"emission_id": "e1", "value_kg": 500.5}],
        None,
    )

    # Mock Gemini
    mock_gemini = AsyncMock()

    report_text = """
1. Boundary & Methodology
Content here. 500.5 kg CO2e
2. Scope Breakdown
Content here.
3. Hotspot Identification
Content here.
4. Recommendations
Content here.
5. Data Quality Disclosure
Content here.
6. Conclusion
Content here.
7. Executive Summary
Content here.
8. Emissions by Facility
Content here.
9. Trend Analysis
Content here.
10. Appendix
Content here.
"""
    mock_gemini.return_value = report_text

    # Mock S3
    mock_s3 = MagicMock()

    with patch("app.services.report_service.call_gemini", mock_gemini), patch(
        "app.api.v1.reports.s3_client", mock_s3
    ), patch("app.api.v1.reports.generate_pdf", return_value=b"fake_pdf"):

        await generate_report_background(
            "r1",
            "user-1",
            "Company X",
            "2023-01-01",
            "2023-12-31",
            mock_reports_repo,
            mock_emissions_repo,
        )

        # Verify reports repo updated to COMPLETED
        calls = mock_reports_repo.put_item.call_args_list
        item_put = calls[-1][0][0]
        assert item_put["status"] == "COMPLETED"
        assert "pdf_url" in item_put

        # Validate that the generated report text passes the guardrails
        # and has 10 sections.
        assert "1. Boundary & Methodology" in report_text
        assert "10. Appendix" in report_text

        emissions = [{"value_kg": 500.5}]
        assert validate_report_numbers(report_text, emissions) is True
