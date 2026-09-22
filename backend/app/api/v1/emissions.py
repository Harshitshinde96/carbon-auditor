from fastapi import APIRouter
from typing import Dict, Any
from app.core.config import settings
from app.repositories.dynamo_repo import DynamoRepository
from boto3.dynamodb.conditions import Key

router = APIRouter()


def get_db():
    return DynamoRepository(settings.DYNAMO_TABLE_EMISSIONS)


@router.get("/summary")
def get_emissions_summary() -> Dict[str, Any]:
    repo = get_db()

    # Query the base table using the primary partition key `company_id`
    items, _ = repo.query(
        key_condition_expression=Key("company_id").eq("mock_company"),
    )

    if not items:
        return {
            "status": "success",
            "data": {
                "total_co2e_kg": 0,
                "breakdown": {"SCOPE_1": 0, "SCOPE_2": 0, "SCOPE_3": 0},
            },
        }

    scope_totals = {"SCOPE_1": 0.0, "SCOPE_2": 0.0, "SCOPE_3": 0.0}
    total = 0.0

    for item in items:
        scope = item.get("scope")
        amount = float(item.get("co2e_kg", 0.0))
        if scope in scope_totals:
            scope_totals[scope] += amount
            total += amount

    return {
        "status": "success",
        "data": {"total_co2e_kg": total, "breakdown": scope_totals},
    }
