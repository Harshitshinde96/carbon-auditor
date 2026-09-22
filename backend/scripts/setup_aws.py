import boto3
import time
import os

def setup_aws_resources():
    session = boto3.Session(
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        region_name="ap-south-1"
    )

    dynamodb = session.client('dynamodb')
    s3 = session.client('s3')

    # 1. Create S3 Bucket
    bucket_name = "carbon-auditor-uploads-prod" # Unique bucket name
    try:
        print(f"Creating S3 Bucket: {bucket_name}")
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': 'ap-south-1'}
        )
        print("S3 Bucket created successfully.")
    except Exception as e:
        print(f"S3 Bucket error (might already exist): {e}")

    # 2. Create DynamoDB Tables
    tables = [
        {"TableName": "carbon-users", "KeySchema": [{"AttributeName": "company_id", "KeyType": "HASH"}], "AttributeDefinitions": [{"AttributeName": "company_id", "AttributeType": "S"}]},
        {"TableName": "carbon-bills", "KeySchema": [{"AttributeName": "company_id", "KeyType": "HASH"}, {"AttributeName": "bill_id", "KeyType": "RANGE"}], "AttributeDefinitions": [{"AttributeName": "company_id", "AttributeType": "S"}, {"AttributeName": "bill_id", "AttributeType": "S"}]},
        {"TableName": "carbon-emissions", "KeySchema": [{"AttributeName": "company_id", "KeyType": "HASH"}, {"AttributeName": "emission_date", "KeyType": "RANGE"}], "AttributeDefinitions": [{"AttributeName": "company_id", "AttributeType": "S"}, {"AttributeName": "emission_date", "AttributeType": "S"}]},
        {"TableName": "carbon-settings", "KeySchema": [{"AttributeName": "company_id", "KeyType": "HASH"}], "AttributeDefinitions": [{"AttributeName": "company_id", "AttributeType": "S"}]},
        {"TableName": "carbon-reports", "KeySchema": [{"AttributeName": "company_id", "KeyType": "HASH"}, {"AttributeName": "report_id", "KeyType": "RANGE"}], "AttributeDefinitions": [{"AttributeName": "company_id", "AttributeType": "S"}, {"AttributeName": "report_id", "AttributeType": "S"}]},
    ]

    for table in tables:
        try:
            print(f"Creating DynamoDB Table: {table['TableName']}")
            dynamodb.create_table(
                TableName=table['TableName'],
                KeySchema=table['KeySchema'],
                AttributeDefinitions=table['AttributeDefinitions'],
                BillingMode='PAY_PER_REQUEST'
            )
            print(f"Table {table['TableName']} creation initiated.")
        except Exception as e:
            print(f"Table {table['TableName']} error (might already exist): {e}")
            
    # Also create the GSI for bills if needed by the app
    # Wait for carbon-bills to be ACTIVE first
    try:
        print("Waiting for carbon-bills to be ACTIVE to create GSI...")
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName='carbon-bills')
        
        # Check if GSI exists
        desc = dynamodb.describe_table(TableName='carbon-bills')
        if not desc['Table'].get('GlobalSecondaryIndexes'):
            dynamodb.update_table(
                TableName='carbon-bills',
                AttributeDefinitions=[
                    {"AttributeName": "company_id", "AttributeType": "S"},
                    {"AttributeName": "uploaded_at", "AttributeType": "S"}
                ],
                GlobalSecondaryIndexUpdates=[
                    {
                        "Create": {
                            "IndexName": "UploadDateIndex",
                            "KeySchema": [
                                {"AttributeName": "company_id", "KeyType": "HASH"},
                                {"AttributeName": "uploaded_at", "KeyType": "RANGE"}
                            ],
                            "Projection": {"ProjectionType": "ALL"}
                        }
                    }
                ]
            )
            print("GSI UploadDateIndex creation initiated on carbon-bills.")
    except Exception as e:
        print(f"Error creating GSI on carbon-bills: {e}")

if __name__ == "__main__":
    setup_aws_resources()
