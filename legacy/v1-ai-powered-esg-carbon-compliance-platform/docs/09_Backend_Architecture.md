# Carbon-Auditor: Backend Architecture

## 1. Purpose

This document outlines the architectural structure, design patterns, and internal directory layout of the FastAPI Python backend for the Carbon-Auditor platform.

## 2. Global Architecture Pattern

The backend strictly adheres to a **Layered Architecture** (often referred to as an Onion or Hexagonal Architecture variant) to ensure a clean separation of concerns.

* **Controllers (Routers)**: The entry point. Handles HTTP requests, parses payloads using Pydantic, and returns HTTP responses.
* **Services**: The brain. Contains all business rules, calculations, and orchestrates calls to external APIs or Repositories.
* **Repositories**: The data layer. Abstracts away DynamoDB and S3 interactions. Services do not know *how* data is stored, only that it is stored.
* **Models**: Pydantic models for request/response validation and internal data passing.

## 3. Directory Structure

```text
backend/
├── main.py                 # FastAPI application instance & Mangum wrapper
├── requirements.txt        # Python dependencies
├── app/
│   ├── api/                # Controllers / Routers
│   │   ├── v1/
│   │   │   ├── auth.py
│   │   │   ├── bills.py
│   │   │   ├── chat.py
│   │   │   └── emissions.py
│   ├── core/               # Configuration & Security
│   │   ├── config.py       # Pydantic BaseSettings (Env vars)
│   │   ├── security.py     # JWT generation/validation
│   │   └── exceptions.py   # Custom global exception handlers
│   ├── services/           # Business Logic
│   │   ├── ocr_service.py
│   │   ├── calc_engine.py  # Deterministic Carbon Engine
│   │   └── rag_service.py
│   ├── repositories/       # Data Access Layer
│   │   ├── dynamo_repo.py
│   │   └── s3_repo.py
│   ├── models/             # Pydantic Schemas
│   │   ├── request.py
│   │   └── response.py
│   └── utils/              # Helper functions (e.g., logging setup)
```

## 4. Key Components Detail

### 4.1. Dependency Injection
FastAPI's native Dependency Injection (`Depends()`) is used to inject Repositories into Services, and Services into Controllers. This makes unit testing significantly easier by allowing mock injections.

### 4.2. Validation & Serialization
Pydantic is used exclusively for all data validation. Every API request body must have a corresponding Pydantic model in `models/request.py`.

### 4.3. Exception Handling
Instead of returning `HTTPException` directly from Services, custom Python exceptions are raised (e.g., `BillNotFoundError`, `OCRProcessingError`). A global exception handler in `main.py` intercepts these and maps them to standard HTTP responses (404, 500).

## 5. Service Definitions

### `calc_engine.py` (Carbon Calculation Engine)
* **Input**: `ExtractedBillData` (Pydantic model containing consumption and unit).
* **Output**: `CalculatedEmission` (Pydantic model containing CO₂e and Scope).
* **Business Rules**: Strictly implements GHG protocol deterministic math. No external API calls.
* **Failure Scenarios**: Raises `UnsupportedUtilityTypeError` if an unknown utility is passed.

### `ocr_service.py`
* **Input**: S3 Object Key.
* **Dependencies**: `s3_repo.py`, PaddleOCR library, Gemini Flash SDK.
* **Failure Scenarios**: Handles PaddleOCR crashes (Timeout) or Gemini JSON parsing failures.

## 6. Configuration Management

Configuration is handled using Pydantic `BaseSettings` in `core/config.py`. It automatically reads from `.env` files locally and Environment Variables in AWS Lambda.

```python
class Settings(BaseSettings):
    PROJECT_NAME: str = "Carbon-Auditor"
    JWT_SECRET: str
    GEMINI_API_KEY: str
    AWS_REGION: str = "us-east-1"
    
    class Config:
        env_file = ".env"
```

## 7. Developer Notes
* **Mangum**: The `main.py` file must wrap the FastAPI app with `Mangum` to allow it to run seamlessly inside an AWS Lambda function triggered by API Gateway.
* **Local Development**: Run using `uvicorn app.main:app --reload`. Mock AWS services using `moto` or `localstack` if necessary.
