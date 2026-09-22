import json
import boto3
import base64
import uuid
import os
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS Clients
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

# Configuration
BUCKET_NAME = "carbon-dev-bills"
TABLE_NAME = "carbon-dev-bill-metadata"

table = dynamodb.Table(TABLE_NAME)


def response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }


def lambda_handler(event, context):
    logger.info("Upload Lambda triggered.")
    try:
        body = json.loads(event["body"])

        user_id = body.get("userId")
        bill_type = body.get("billType")
        file_name = body.get("fileName")
        file_data = body.get("fileData")

        if not user_id:
            return response(400, {"message": "userId is required"})

        if not bill_type:
            return response(400, {"message": "billType is required"})

        if not file_name:
            return response(400, {"message": "fileName is required"})

        if not file_data:
            return response(400, {"message": "fileData is required"})

        # Generate Bill ID
        bill_id = str(uuid.uuid4())

        # Get file extension
        extension = file_name.split(".")[-1]

        # Create S3 Key
        current_date = datetime.now()

        s3_key = (
            f"uploads/"
            f"{user_id}/"
            f"{current_date.year}/"
            f"{current_date.month:02d}/"
            f"{bill_id}.{extension}"
        )

        # Decode Base64
        logger.info(f"Decoding base64 data for {file_name}")
        file_bytes = base64.b64decode(file_data)

        content_type = "application/octet-stream"

        if extension.lower() == "pdf":
            content_type = "application/pdf"
        elif extension.lower() == "png":
            content_type = "image/png"
        elif extension.lower() in ["jpg", "jpeg"]:
            content_type = "image/jpeg"

        logger.info(f"Uploading file to S3: {BUCKET_NAME}/{s3_key}")
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=file_bytes,
            ContentType=content_type
        )
        logger.info("Successfully uploaded to S3.")

        # Store Metadata in DynamoDB
        logger.info(f"Writing metadata to DynamoDB table: {TABLE_NAME}")
        table.put_item(
            Item={
                "billId": bill_id,
                "userId": user_id,
                "billType": bill_type,
                "fileName": file_name,
                "s3Key": s3_key,

                "processingStatus": "UPLOADED",

                "carbonEmission": 0,
                "unitsConsumed": 0,
                "billAmount": 0,

                "reportGenerated": False,

                "uploadedAt": datetime.utcnow().isoformat(),
                "updatedAt": datetime.utcnow().isoformat()
            }
        )
        logger.info("Successfully wrote to DynamoDB.")

        return response(200, {
            "success": True,
            "message": "Bill uploaded successfully.",
            "billId": bill_id,
            "processingStatus": "UPLOADED"
        })

    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}", exc_info=True)
        return response(500, {
            "message": str(e)
        })
