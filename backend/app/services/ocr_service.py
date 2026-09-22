import json
import logging
from typing import Dict, Any
from markitdown import MarkItDown

from app.core.exceptions import OCRProcessingError
from app.core.llm_client import OpenRouterClient
from app.core.config import settings
from app.repositories.dynamo_repo import DynamoRepository

logger = logging.getLogger(__name__)


def process_bill_ocr(file_path: str, bill_id: str) -> Dict[str, Any]:
    """
    1. Converts ANY document to Markdown using Microsoft MarkItDown.
    2. Triggers FAILED_OCR_QUALITY if < 20 words.
    3. Calls OpenRouter to extract JSON (utility_type, consumption, unit, cost, period_start, period_end).
    4. Retries twice on malformed JSON.
    """

    # 1. Document to Markdown conversion
    md = MarkItDown()

    try:
        result = md.convert(file_path)
        all_text = result.text_content
    except Exception as e:
        raise OCRProcessingError(f"MarkItDown conversion failed: {str(e)}")

    words = all_text.split()
    if len(words) < 20:
        raise OCRProcessingError("FAILED_OCR_QUALITY: Fewer than 20 words extracted")

    # 2. OpenRouter Extraction
    llm = OpenRouterClient()

    prompt = f"""
    Extract the following billing information from the text:
    - utility_type (String: must be 'electricity', 'natural gas', or something else)
    - consumption (Number)
    - unit (String)
    - cost (Number)
    - period_start (YYYY-MM-DD)
    - period_end (YYYY-MM-DD)
    
    Return ONLY a valid JSON object matching this schema. Do NOT wrap it in markdown. Do NOT add any extra text.
    
    Extracted Text:
    {all_text}
    """

    retries = 2
    for attempt in range(retries + 1):
        import asyncio
        # We must run the async client in a synchronous context here, 
        # or use a new event loop since process_bill_ocr is called synchronously in background task.
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # This should not happen in a typical background task thread, but just in case
                import nest_asyncio
                nest_asyncio.apply()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        text = asyncio.run(llm.generate_content(prompt))

        try:
            data = llm.extract_json(text)

            # Basic validation
            required_keys = {
                "utility_type",
                "consumption",
                "unit",
                "cost",
                "period_start",
                "period_end",
            }
            if not required_keys.issubset(data.keys()):
                raise ValueError("Missing required keys")

            return data

        except (ValueError, RuntimeError) as e:
            if attempt == retries:
                raise OCRProcessingError(
                    "Failed to extract valid JSON from OpenRouter"
                ) from e
            prompt += f"\nYour last response was invalid JSON or missing keys. Fix it. Error: {str(e)}"
    raise RuntimeError("Unexpected end of retry loop")


def process_bill_background_task(
    file_path: str, bill_id: str, company_id: str, table_name: str = "carbon-bills"
):
    from app.repositories.dynamo_repo import DynamoRepository
    from app.services.calc_engine import calculate_emissions

    repo = DynamoRepository(table_name)
    key = {"company_id": company_id, "bill_id": bill_id}

    try:
        item = repo.get_item(key)
        if not item:
            item = {
                **key,
                "uploaded_at": "unknown",
                "s3_key": "unknown",
                "filename": "unknown",
            }

        assert item is not None
        item["status"] = "PROCESSING"
        repo.put_item(item)

        extracted = process_bill_ocr(file_path, bill_id)

        emissions = calculate_emissions(
            utility_type=extracted["utility_type"],
            consumption=extracted["consumption"],
            unit=extracted["unit"],
        )

        from decimal import Decimal

        extracted_decimal = {
            "utility_type": extracted["utility_type"].upper(),
            "consumption": Decimal(str(extracted["consumption"])),
            "unit": extracted["unit"],
            "cost": Decimal(str(extracted["cost"])) if "cost" in extracted else None,
            "billing_period_start": extracted.get("period_start"),
            "billing_period_end": extracted.get("period_end"),
        }

        ut_lower = extracted["utility_type"].strip().lower()
        if ut_lower == "electricity":
            scope = "SCOPE_2"
            factor_used = Decimal("0.385")
        elif ut_lower == "natural gas":
            scope = "SCOPE_1"
            factor_used = Decimal("5.3")
        else:
            scope = "SCOPE_3"
            factor_used = Decimal("0.344")

        assert item is not None
        item["status"] = "COMPLETED"
        item["extracted_data"] = extracted_decimal
        item["emissions"] = {
            "calculated_co2e_kg": Decimal(str(emissions)),
            "scope": scope,
            "factor_used": factor_used,
        }
        repo.put_item(item)

        # Also store the emissions in the carbon-emissions table
        emissions_repo = DynamoRepository(settings.DYNAMO_TABLE_EMISSIONS)
        # Use a fallback date if period_start is not available
        emission_date = extracted.get("period_start")
        if not emission_date:
            import datetime
            emission_date = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")

        emissions_repo.put_item({
            "company_id": company_id,
            "emission_date": f"{emission_date}#{bill_id}", # Combine date and bill_id to make range key unique per bill
            "bill_id": bill_id,
            "scope": scope,
            "co2e_kg": Decimal(str(emissions)),
            "utility_type": extracted["utility_type"].upper(),
        })

    except OCRProcessingError as e:
        status = "FAILED_OCR_QUALITY" if "FAILED_OCR_QUALITY" in str(e) else "FAILED"
        if "item" in locals():
            assert item is not None
            item["status"] = status
            item["error_message"] = str(e)
            repo.put_item(item)
    except Exception as e:  # pragma: no cover
        if "item" in locals():
            assert item is not None
            item["status"] = "FAILED"
            item["error_message"] = f"Unexpected error: {str(e)}"
            repo.put_item(item)
