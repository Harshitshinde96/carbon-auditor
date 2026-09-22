import pytest
import boto3
from moto import mock_aws

# We'll implement the repo next
from app.repositories.dynamo_repo import DynamoRepository


@pytest.fixture
def aws_credentials(monkeypatch):
    """Mocked AWS Credentials for moto."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_REGION", "us-east-1")


@pytest.fixture
def mock_dynamodb(aws_credentials):
    with mock_aws():
        dynamodb = boto3.client("dynamodb", region_name="us-east-1")

        # Create mocked carbon-bills table per DESIGN.md §2.2
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
        yield dynamodb


def test_put_and_get_item(mock_dynamodb):
    repo = DynamoRepository(table_name="carbon-bills")
    item = {
        "company_id": "comp-123",
        "bill_id": "bill-456",
        "upload_date": "2026-09-01T00:00:00Z",
        "status": "COMPLETED",
    }

    # Put item
    repo.put_item(item)

    # Get item
    retrieved = repo.get_item(key={"company_id": "comp-123", "bill_id": "bill-456"})

    assert retrieved is not None
    assert retrieved["status"] == "COMPLETED"


def test_get_nonexistent_item(mock_dynamodb):
    repo = DynamoRepository(table_name="carbon-bills")
    retrieved = repo.get_item(key={"company_id": "comp-999", "bill_id": "bill-999"})
    assert retrieved is None


def test_query_items(mock_dynamodb):
    repo = DynamoRepository(table_name="carbon-bills")

    # Insert multiple items — use a unique company_id to avoid cross-test leaks
    items = [
        {
            "company_id": "query-test-co",
            "bill_id": "bill-001",
            "upload_date": "2026-09-01T10:00:00Z",
        },
        {
            "company_id": "query-test-co",
            "bill_id": "bill-002",
            "upload_date": "2026-09-02T10:00:00Z",
        },
        {
            "company_id": "other-co",
            "bill_id": "bill-003",
            "upload_date": "2026-09-03T10:00:00Z",
        },
    ]
    for item in items:
        repo.put_item(item)

    from boto3.dynamodb.conditions import Key

    # Query by partition key only
    results, _ = repo.query(
        key_condition_expression=Key("company_id").eq("query-test-co"),
    )

    assert len(results) == 2
    bill_ids = [r["bill_id"] for r in results]
    assert "bill-001" in bill_ids
    assert "bill-002" in bill_ids
    assert "bill-003" not in bill_ids


def test_query_index(mock_dynamodb):
    repo = DynamoRepository(table_name="carbon-bills")

    repo.put_item(
        {
            "company_id": "idx-test-co",
            "bill_id": "bill-001",
            "upload_date": "2026-09-01T10:00:00Z",
        }
    )
    repo.put_item(
        {
            "company_id": "idx-test-co",
            "bill_id": "bill-002",
            "upload_date": "2026-09-02T10:00:00Z",
        }
    )

    from boto3.dynamodb.conditions import Key

    # Query GSI UploadDateIndex using proper Key conditions
    results, _ = repo.query(
        key_condition_expression=Key("company_id").eq("idx-test-co")
        & Key("upload_date").gt("2026-09-01T15:00:00Z"),
        index_name="UploadDateIndex",
    )

    assert len(results) == 1
    assert results[0]["bill_id"] == "bill-002"
