import pytest
from unittest.mock import patch, MagicMock
from app.services.ocr_service import process_bill_background_task
from app.repositories.dynamo_repo import DynamoRepository

import boto3
from moto import mock_aws
from decimal import Decimal


@pytest.fixture
def mock_dynamodb():
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        dynamodb.create_table(
            TableName="carbon-bills",
            KeySchema=[
                {"AttributeName": "company_id", "KeyType": "HASH"},
                {"AttributeName": "bill_id", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "company_id", "AttributeType": "S"},
                {"AttributeName": "bill_id", "AttributeType": "S"},
                {"AttributeName": "upload_date", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "UploadDateIndex",
                    "KeySchema": [
                        {"AttributeName": "company_id", "KeyType": "HASH"},
                        {"AttributeName": "upload_date", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        dynamodb.create_table(
            TableName="carbon-emissions",
            KeySchema=[
                {"AttributeName": "company_id", "KeyType": "HASH"},
                {"AttributeName": "emission_date", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "company_id", "AttributeType": "S"},
                {"AttributeName": "emission_date", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        yield dynamodb


@pytest.fixture
def mock_markitdown():
    with patch("app.services.ocr_service.MarkItDown") as MockMID:
        mock_instance = MockMID.return_value
        mock_result = MagicMock()
        mock_result.text_content = "word " * 25
        mock_instance.convert.return_value = mock_result
        yield mock_instance


@pytest.fixture
def mock_gemini():
    with patch("app.services.ocr_service.genai") as mock_genai:
        mock_model = mock_genai.GenerativeModel.return_value
        mock_model.generate_content.return_value.text = '{"utility_type": "Electricity", "consumption": 100, "unit": "kWh", "cost": 50.0, "period_start": "2024-01-01", "period_end": "2024-01-31"}'
        yield mock_genai


def test_background_task_success(mock_dynamodb, mock_markitdown, mock_gemini):
    repo = DynamoRepository("carbon-bills")

    repo.put_item(
        {"company_id": "mock_company", "bill_id": "test_123", "status": "PENDING"}
    )

    process_bill_background_task(
        "dummy.xlsx", "test_123", "mock_company", "carbon-bills"
    )

    updated = repo.get_item({"company_id": "mock_company", "bill_id": "test_123"})
    assert updated["status"] == "COMPLETED"
    assert updated["extracted_data"]["utility_type"] == "ELECTRICITY"
    assert updated["emissions"]["calculated_co2e_kg"] == Decimal("38.5")
    assert updated["emissions"]["scope"] == "SCOPE_2"


def test_background_task_failure(mock_dynamodb, mock_markitdown, mock_gemini):
    repo = DynamoRepository("carbon-bills")
    repo.put_item(
        {"company_id": "mock_company", "bill_id": "test_456", "status": "PENDING"}
    )

    mock_result = MagicMock()
    mock_result.text_content = "word " * 10
    mock_markitdown.convert.return_value = mock_result

    process_bill_background_task(
        "dummy.docx", "test_456", "mock_company", "carbon-bills"
    )

    updated = repo.get_item({"company_id": "mock_company", "bill_id": "test_456"})
    assert updated["status"] == "FAILED_OCR_QUALITY"
    assert "error_message" in updated
