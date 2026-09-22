from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any
from app.repositories.dynamo_repo import DynamoRepository
from app.core.config import settings
import uuid
import datetime
from app.services.report_service import generate_report_content, generate_pdf
import boto3

router = APIRouter(prefix="/reports", tags=["Reports"])

# Initialize S3
s3_client = boto3.client("s3", region_name=settings.AWS_REGION)


def get_reports_repo():
    return DynamoRepository(settings.DYNAMO_TABLE_REPORTS)


def get_emissions_repo():
    return DynamoRepository(settings.DYNAMO_TABLE_EMISSIONS)


class GenerateReportRequest(BaseModel):
    period_start: str
    period_end: str


async def generate_report_background(
    report_id: str,
    company_id: str,
    company_name: str,
    period_start: str,
    period_end: str,
    reports_repo: DynamoRepository,
    emissions_repo: DynamoRepository,
):
    try:
        from boto3.dynamodb.conditions import Key

        # 1. Fetch emissions data
        # Query base table carbon-emissions by company_id and emission_date between period_start and period_end
        items, _ = emissions_repo.query(
            key_condition_expression=Key("company_id").eq(company_id)
            & Key("emission_date").between(period_start, f"{period_end}z")
        )

        if not items:
            reports_repo.put_item(
                {
                    "company_id": company_id,
                    "report_id": report_id,
                    "status": "FAILED",
                    "error_message": "No emissions data found for range",
                }
            )
            return

        # 2. Generate report text with Gemini
        report_text = await generate_report_content(
            company_name, period_start, period_end, items
        )

        # 3. Assemble PDF
        pdf_bytes = generate_pdf(report_text, company_name)

        # 4. Upload to S3
        s3_key = f"reports/{company_id}/{report_id}.pdf"
        import tempfile
        import os
        from app.repositories.s3_repo import S3Repository
        
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, s3_key.replace("/", "_"))
        
        with open(temp_path, "wb") as f:
            f.write(pdf_bytes)

        # Upload to S3
        s3_repo = S3Repository(settings.S3_UPLOAD_BUCKET)
        with open(temp_path, "rb") as f:
            s3_repo.upload_file(f, s3_key, content_type="application/pdf")

        # Create a proxy endpoint to serve the PDF
        pdf_url = f"{settings.NEXT_PUBLIC_API_BASE_URL if hasattr(settings, 'NEXT_PUBLIC_API_BASE_URL') else 'http://localhost:8000'}/api/v1/reports/{report_id}/file"


        reports_repo.put_item(
            {
                "company_id": company_id,
                "report_id": report_id,
                "status": "COMPLETED",
                "pdf_url": pdf_url,
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
        )

    except Exception as e:
        reports_repo.put_item(
            {
                "company_id": company_id,
                "report_id": report_id,
                "status": "FAILED",
                "error_message": str(e),
            }
        )


@router.post("/generate", status_code=202)
async def generate_report(
    req: GenerateReportRequest,
    background_tasks: BackgroundTasks,
    repo: DynamoRepository = Depends(get_reports_repo),
    emissions_repo: DynamoRepository = Depends(get_emissions_repo),
):
    company_id = "mock_company"

    # Validate date range
    try:
        start_date = datetime.date.fromisoformat(req.period_start)
        end_date = datetime.date.fromisoformat(req.period_end)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD."
        )

    if start_date >= end_date:
        raise HTTPException(
            status_code=400, detail="period_start must be before period_end"
        )

    if (end_date - start_date).days > 366:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 366 days")

    # Check concurrent identical request (prevent multiple IN_PROGRESS reports for same company)
    from boto3.dynamodb.conditions import Key
    items, _ = repo.query(
        key_condition_expression=Key("company_id").eq(company_id)
    )
    for item in items:
        if item.get("status") == "IN_PROGRESS":
            raise HTTPException(
                status_code=409, detail="A report is already being generated"
            )

    report_id = str(uuid.uuid4())

    # Save IN_PROGRESS
    repo.put_item(
        {
            "company_id": company_id,
            "report_id": report_id,
            "status": "IN_PROGRESS",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
    )

    background_tasks.add_task(
        generate_report_background,
        report_id,
        company_id,
        "User Company",  # Placeholder, maybe fetch from user profile
        req.period_start,
        req.period_end,
        repo,
        emissions_repo,
    )

    return {"report_id": report_id, "status": "IN_PROGRESS"}


@router.get("/{report_id}")
def get_report(
    report_id: str,
    repo: DynamoRepository = Depends(get_reports_repo),
):
    company_id = "mock_company"
    item = repo.get_item({"company_id": company_id, "report_id": report_id})
    if not item:
        raise HTTPException(status_code=404, detail="Report not found")

    return item


@router.get("/{report_id}/file")
def get_report_file(
    report_id: str,
    repo: DynamoRepository = Depends(get_reports_repo),
):
    from fastapi import Response
    from app.repositories.s3_repo import S3Repository
    
    company_id = "mock_company"
    item = repo.get_item({"company_id": company_id, "report_id": report_id})
    if not item:
        raise HTTPException(status_code=404, detail="Report not found")
        
    s3_key = f"reports/{company_id}/{report_id}.pdf"
    s3_repo = S3Repository(settings.S3_UPLOAD_BUCKET)
    
    try:
        pdf_bytes = s3_repo.download_file(s3_key)
    except Exception:
        import tempfile
        import os
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, s3_key.replace("/", "_"))
        if os.path.exists(temp_path):
            with open(temp_path, "rb") as f:
                pdf_bytes = f.read()
        else:
            raise HTTPException(status_code=404, detail="Report file not found")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="report_{report_id}.pdf"'}
    )
