# Carbon-Auditor: Error Handling

## 1. Purpose

This document outlines the global error handling strategy for the Carbon-Auditor platform. A consistent error-handling approach ensures predictable API responses for the frontend, simplifies debugging, and prevents sensitive system information from leaking to users.

## 2. Backend Error Strategy (FastAPI)

We avoid throwing bare HTTP exceptions from within business logic (Services). Instead, we define custom domain-specific Python exceptions. A global exception handler at the application level catches these and formats a standardized HTTP response.

### 2.1. Global Exception Handler

In `app/main.py`, we register an exception handler:

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import CarbonBaseException

@app.exception_handler(CarbonBaseException)
async def custom_exception_handler(request: Request, exc: CarbonBaseException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "code": exc.status_code,
            "message": exc.message,
            "details": exc.details
        }
    )
```

### 2.2. Custom Exception Hierarchy

All custom exceptions inherit from `CarbonBaseException`.

*   `AuthenticationError` (401 Unauthorized): Used when JWT is missing or invalid.
*   `AuthorizationError` (403 Forbidden): Used when a user tries to access a resource they do not own.
*   `ResourceNotFoundError` (404 Not Found): Used when querying DynamoDB returns no items.
*   `ValidationProcessingError` (422 Unprocessable Entity): Used when Pydantic validation passes, but business logic validation fails (e.g., negative consumption values).
*   `OCRProcessingError` (500 Internal Server Error): Used when PaddleOCR or Gemini fails to extract data. *Details should be logged to CloudWatch, but hidden from the user response.*

## 3. Frontend Error Strategy

The frontend SPA must gracefully handle API errors without crashing.

### 3.1. API Interceptors

If using `axios` or native `fetch`, implement a global response interceptor.

*   **401 Unauthorized**: Automatically clear local storage and redirect the user to the `/login` page.
*   **500 Internal Server Error**: Display a generic, user-friendly toast notification: *"Something went wrong on our end. Our team has been notified."*

### 3.2. Form Validation

*   Client-side validation (e.g., checking if email is valid before submitting) should be the first line of defense to reduce unnecessary API calls.
*   If the backend returns a `400 Bad Request` with `details`, the frontend should map those details to the specific form fields and highlight them in red.

## 4. Lambda & CloudWatch Error Logging

*   **Unhandled Exceptions**: If an unhandled Python exception occurs (e.g., a `KeyError`), AWS Lambda will automatically log the full stack trace to Amazon CloudWatch.
*   **Structured Logging**: Use the Python `logging` module configured to output JSON. This makes it easier to search and filter logs in CloudWatch Insights.

Example JSON Log:
```json
{
  "level": "ERROR",
  "timestamp": "2023-10-15T08:30:00Z",
  "request_id": "req-123",
  "error": "OCRProcessingError",
  "message": "PaddleOCR timed out processing bill_id: abc-456"
}
```

## 5. Dead Letter Queues (DLQ)

While the current architecture uses synchronous API Gateway calls, future async integrations (e.g., EventBridge triggers) must configure a Dead Letter Queue (Amazon SQS). If an async Lambda function fails 3 times, the event payload is sent to the DLQ for manual inspection and replay, ensuring zero data loss.
