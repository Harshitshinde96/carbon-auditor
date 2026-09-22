# Carbon-Auditor: Carbon Calculation Engine

## 1. Purpose

This document details the core business logic of the Carbon-Auditor platform: The Carbon Calculation Engine. 

> [!CAUTION]
> **Strict Architectural Rule:** No AI or LLM is allowed to perform carbon calculations. AI is notoriously unreliable for deterministic math. All calculations must be executed using strict Python business logic based on established GHG Protocol factors.

## 2. Overview

The Calculation Engine is a deterministic service module (`calc_engine.py`) in the backend. It receives structured, validated consumption data from the OCR pipeline (or manual entry) and calculates the equivalent CO₂ emissions (CO₂e).

## 3. Emission Factors

During development, a static mapping of standardized emission factors is used. In production, these factors could be fetched from a dynamic database (like the EPA eGRID API or DEFRA).

**Current Static Factors (Development Mode):**
*   **Electricity (US Average)**: 0.385 kg CO₂e / kWh
*   **Natural Gas**: 5.3 kg CO₂e / Therm
*   **Water (Treatment & Delivery)**: 0.344 kg CO₂e / 1000 Gallons

## 4. Scope Classification

The engine automatically classifies the emission based on the `utility_type` extracted from the bill.

| Utility Type | GHG Scope | Category |
| :--- | :--- | :--- |
| `ELECTRICITY` | Scope 2 | Purchased Electricity |
| `NATURAL_GAS` | Scope 1 | Stationary Combustion |
| `WATER` | Scope 3 | Purchased Goods & Services (Water) |

## 5. Calculation Logic

The mathematical formula is straightforward:
`Emissions (kg CO₂e) = Consumption * Emission Factor`

### 5.1. Input (Pydantic Model)
```python
class ExtractedBillData(BaseModel):
    utility_type: UtilityTypeEnum
    consumption: float
    unit: str
```

### 5.2. Execution Flow

1.  **Validation**: Verify the `unit` matches the expected unit for the `utility_type`. If a bill reports electricity in "Joules" instead of "kWh", the engine must either convert it or raise an `UnsupportedUnitError`.
2.  **Lookup**: Retrieve the emission factor for the given `utility_type`.
3.  **Calculation**: Perform the multiplication.
4.  **Formatting**: Round the result to 2 decimal places.
5.  **Output**: Return the `CalculatedEmission` model containing the kg CO₂e, Scope, and Factor used.

## 6. Edge Cases and Error Handling

| Scenario | Engine Action |
| :--- | :--- |
| Negative Consumption | Raise `InvalidConsumptionError` |
| Unknown Utility Type | Raise `UnsupportedUtilityTypeError` |
| Unit Mismatch (e.g., Gas in kWh) | Attempt conversion if programmed, otherwise raise `UnitMismatchError` and flag for manual review. |

## 7. Future Production Upgrades

*   **Location-Based Factors**: Electricity factors vary wildly by region. Future versions should parse the zip code from the utility bill address and query the EPA eGRID database to get highly accurate, region-specific grid emission factors.
*   **Market-Based Factors**: Add support for Renewable Energy Certificates (RECs). If a company provides proof of 100% renewable energy purchasing, the Scope 2 market-based calculation will override the location-based calculation and result in 0 kg CO₂e.
