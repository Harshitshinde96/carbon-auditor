import os
import uuid
import datetime
import boto3
import tempfile
import base64
import json
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse
from typing import Dict, Any, Optional

from app.core.config import settings
from app.repositories.dynamo_repo import DynamoRepository
from app.services.ocr_service import process_bill_background_task

router = APIRouter()
s3_client = boto3.client("s3", region_name=settings.AWS_REGION)

# Max file size 15MB
MAX_FILE_SIZE = 15 * 1024 * 1024

ALLOWED_MIME_TYPES = [
    "application/pdf",
    "image/png",
    "image/jpeg",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx
    "text/csv",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # pptx
]


def get_db():
    return DynamoRepository(settings.DYNAMO_TABLE_BILLS)


@router.post("/upload", status_code=202)
async def upload_bill(
    background_tasks: BackgroundTasks, bill_file: UploadFile = File(...)
) -> Dict[str, Any]:
    # Check mime type
    if bill_file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported type")

    # Check size by reading content
    content = await bill_file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, detail="File exceeds the 15MB upload limit."
        )

    bill_id = str(uuid.uuid4())
    s3_key = f"uploads/{bill_id}_{bill_file.filename}"

    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, s3_key.replace("/", "_"))
    with open(temp_path, "wb") as f:
        f.write(content)

    # In a real app we upload to S3 here
    # s3_client.put_object(Bucket=settings.S3_UPLOAD_BUCKET, Key=s3_key, Body=content)

    repo = get_db()
    repo.put_item(
        {
            "company_id": "mock_company",  # Would come from auth token
            "bill_id": bill_id,
            "status": "PENDING",
            "uploaded_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "s3_key": s3_key,
            "filename": bill_file.filename,
        }
    )

    background_tasks.add_task(
        process_bill_background_task,
        temp_path,
        bill_id,
        "mock_company",
        settings.DYNAMO_TABLE_BILLS,
    )

    return {
        "status": "success",
        "data": {"bill_id": bill_id, "message": "Bill accepted for processing."},
    }


@router.get("/{bill_id}")
def get_bill(bill_id: str) -> Dict[str, Any]:
    repo = get_db()
    item = repo.get_item({"company_id": "mock_company", "bill_id": bill_id})
    if not item:
        raise HTTPException(status_code=404, detail="Bill not found")

    return {"status": "success", "data": item}


@router.get("/{bill_id}/file")
def get_bill_file(bill_id: str):
    from fastapi.responses import RedirectResponse
    from app.repositories.s3_repo import S3Repository
    repo = get_db()
    item = repo.get_item({"company_id": "mock_company", "bill_id": bill_id})
    if not item or "s3_key" not in item:
        raise HTTPException(status_code=404, detail="Bill file not found")

    s3_key = item["s3_key"]
    s3_repo = S3Repository(settings.S3_UPLOAD_BUCKET)
    signed_url = s3_repo.get_signed_url(s3_key)
    
    return RedirectResponse(url=signed_url)


@router.get("/")
def list_bills(limit: int = Query(20), cursor: Optional[str] = None) -> Dict[str, Any]:
    repo = get_db()

    start_key = None
    if cursor:
        try:
            start_key_json = base64.b64decode(cursor).decode("utf-8")
            start_key = json.loads(start_key_json)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid cursor format")

    from boto3.dynamodb.conditions import Key

    items, next_key = repo.query_index(
        index_name="UploadDateIndex",
        key_condition_expression=Key("company_id").eq("mock_company"),
        limit=limit,
        exclusive_start_key=start_key,
        scan_index_forward=False,
    )

    next_cursor = None
    if next_key:
        next_cursor = base64.b64encode(json.dumps(next_key).encode("utf-8")).decode(
            "utf-8"
        )

    return {
        "status": "success",
        "data": {
            "items": items,
            "next_cursor": next_cursor,
        },
    }


@router.post("/{bill_id}/reprocess")
def reprocess_bill(bill_id: str) -> Dict[str, Any]:
    repo = get_db()
    item = repo.get_item({"company_id": "mock_company", "bill_id": bill_id})

    if not item:
        raise HTTPException(status_code=404, detail="Bill not found")

    if item.get("status") == "PROCESSING" or item.get("status") == "PENDING":
        raise HTTPException(status_code=409, detail="Bill is currently processing")

    # (Background task logic would go here)
    return {"status": "success"}


@router.delete("/{bill_id}")
def delete_bill(bill_id: str) -> Dict[str, Any]:
    repo = get_db()
    key = {"company_id": "mock_company", "bill_id": bill_id}
    item = repo.get_item(key)

    if not item:
        raise HTTPException(status_code=404, detail="Bill not found")

    # Delete from DB
    repo.table.delete_item(Key=key)

    # Attempt to delete file locally
    if "s3_key" in item:
        s3_key = item["s3_key"]
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, s3_key.replace("/", "_"))
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

        # In a real app we'd also delete from S3
        # try:
        #     s3_client.delete_object(Bucket=settings.S3_UPLOAD_BUCKET, Key=s3_key)
        # except Exception:
        #     pass

    # Delete associated emissions data
    if "extracted_data" in item:
        extracted = item["extracted_data"]
        emission_date = extracted.get("billing_period_start")
        if not emission_date:
            # Note: If it fell back to datetime.now() during generation, we won't know the exact date easily.
            # But usually billing_period_start is present.
            # In a real production system, we'd store the exact emission_date key in the bill item to easily delete it.
            pass
        else:
            emissions_repo = DynamoRepository(settings.DYNAMO_TABLE_EMISSIONS)
            try:
                emissions_repo.table.delete_item(
                    Key={
                        "company_id": "mock_company",
                        "emission_date": f"{emission_date}#{bill_id}",
                    }
                )
            except Exception:
                pass

    return {"status": "success", "message": "Bill deleted successfully"}
