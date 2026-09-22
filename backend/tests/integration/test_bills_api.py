import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_s3():
    with patch("app.api.v1.bills.s3_client") as mock:
        yield mock


@pytest.fixture
def mock_repo():
    with patch("app.api.v1.bills.DynamoRepository") as mock:
        yield mock


@pytest.fixture
def mock_background_task():
    with patch("app.api.v1.bills.BackgroundTasks.add_task") as mock:
        yield mock


def test_upload_valid_file(mock_s3, mock_repo, mock_background_task):
    file_content = b"fake pdf content"
    files = {"bill_file": ("test.pdf", file_content, "application/pdf")}

    response = client.post("/api/v1/bills/upload", files=files)

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "success"
    assert "bill_id" in data["data"]

    # Assert background task was scheduled
    assert mock_background_task.call_count == 1
    # Assert repo put_item was called
    assert mock_repo.return_value.put_item.call_count == 1


def test_upload_oversize_file():
    # Make a file exactly 15MB + 1 byte
    oversize_content = b"0" * (15 * 1024 * 1024 + 1)
    files = {"bill_file": ("big.pdf", oversize_content, "application/pdf")}

    response = client.post("/api/v1/bills/upload", files=files)

    assert response.status_code == 400
    assert "exceeds" in response.json()["detail"].lower()


def test_upload_unsupported_file():
    files = {"bill_file": ("test.exe", b"exe content", "application/x-msdownload")}

    response = client.post("/api/v1/bills/upload", files=files)

    assert response.status_code == 400
    assert "unsupported type" in response.json()["detail"].lower()


def test_get_bill_status(mock_repo):
    mock_repo.return_value.get_item.return_value = {
        "bill_id": "test_123",
        "status": "COMPLETED",
        "emissions": 38.5,
    }

    response = client.get("/api/v1/bills/test_123")

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "COMPLETED"
    assert data["data"]["emissions"] == 38.5


def test_get_bills_paginated(mock_repo):
    mock_repo.return_value.query_index.return_value = (
        [{"bill_id": "1"}, {"bill_id": "2"}],
        {"user_id": "mock", "uploaded_at": "123"},
    )

    response = client.get("/api/v1/bills?limit=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["items"]) == 2
    assert "next_cursor" in data["data"]


def test_reprocess_concurrent_conflict(mock_repo):
    # Setup mock to say it's already processing
    mock_repo.return_value.get_item.return_value = {
        "bill_id": "test_123",
        "status": "PROCESSING",
    }

    response = client.post("/api/v1/bills/test_123/reprocess")
    assert response.status_code == 409
    assert "currently processing" in response.json()["detail"].lower()
