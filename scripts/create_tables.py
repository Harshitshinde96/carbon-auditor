"""
DynamoDB table initialisation script.
Reads AWS_ENDPOINT_URL from env so it works both locally (localhost:8001)
and inside Docker Compose (http://dynamodb-local:8000).
"""
import os
import boto3
from botocore.exceptions import ClientError

ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:8001")
REGION = os.environ.get("AWS_REGION", "us-east-1")
ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID", "local")
SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "local")


def get_client():
    return boto3.client(
        "dynamodb",
        endpoint_url=ENDPOINT_URL,
        region_name=REGION,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    )


def create_table_safe(client, **kwargs):
    table_name = kwargs["TableName"]
    try:
        client.create_table(**kwargs)
        print(f"  ✓ Created {table_name}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"  · {table_name} already exists — skipping")
        else:
            print(f"  ✗ Error creating {table_name}: {e}")
            raise


def create_tables():
    print(f"Connecting to DynamoDB at {ENDPOINT_URL} ...")
    client = get_client()

    # carbon-users
    create_table_safe(
        client,
        TableName="carbon-users",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "email", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "EmailIndex",
                "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # carbon-bills
    create_table_safe(
        client,
        TableName="carbon-bills",
        KeySchema=[
            {"AttributeName": "company_id", "KeyType": "HASH"},
            {"AttributeName": "bill_id", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "company_id", "AttributeType": "S"},
            {"AttributeName": "bill_id", "AttributeType": "S"},
            {"AttributeName": "uploaded_at", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "BillIdIndex",
                "KeySchema": [{"AttributeName": "bill_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "UploadDateIndex",
                "KeySchema": [
                    {"AttributeName": "company_id", "KeyType": "HASH"},
                    {"AttributeName": "uploaded_at", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # carbon-emissions
    create_table_safe(
        client,
        TableName="carbon-emissions",
        KeySchema=[
            {"AttributeName": "company_id", "KeyType": "HASH"},
            {"AttributeName": "emission_date", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "company_id", "AttributeType": "S"},
            {"AttributeName": "emission_date", "AttributeType": "S"},
            {"AttributeName": "scope", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "ScopeIndex",
                "KeySchema": [
                    {"AttributeName": "company_id", "KeyType": "HASH"},
                    {"AttributeName": "scope", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # carbon-reports
    create_table_safe(
        client,
        TableName="carbon-reports",
        KeySchema=[
            {"AttributeName": "company_id", "KeyType": "HASH"},
            {"AttributeName": "report_id", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "company_id", "AttributeType": "S"},
            {"AttributeName": "report_id", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "ReportIdIndex",
                "KeySchema": [{"AttributeName": "report_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # carbon-settings
    create_table_safe(
        client,
        TableName="carbon-settings",
        KeySchema=[{"AttributeName": "company_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "company_id", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    print("\nAll tables ready.")


if __name__ == "__main__":
    create_tables()
