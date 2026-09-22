# Carbon-Auditor: API Specification

## 1. Purpose

This document provides a comprehensive specification for all REST APIs exposed by the Carbon-Auditor backend. It defines endpoints, request/response structures, authentication mechanisms, and standard error codes.

## 2. API Design Principles

* **Base Path**: All APIs are prefixed with `/api/v1/`.
* **Content Type**: `application/json` (except for file uploads which use `multipart/form-data`).
* **Authentication**: Bearer JWT passed in the `Authorization` header.
* **Standardization**: Consistent use of HTTP verbs (GET, POST, PUT, DELETE) and standardized response wrappers.

## 3. Global Response Format

**Success Response:**
```json
{
  "status": "success",
  "data": { ... }
}
```

**Error Response:**
```json
{
  "status": "error",
  "code": 400,
  "message": "Invalid request parameters",
  "details": ["Field 'amount' must be positive"]
}
```

## 4. Endpoints

### 4.1. Authentication

#### POST `/api/v1/auth/login`
Authenticates a user and returns a JWT.

* **Method**: POST
* **Headers**: `Content-Type: application/json`
* **Authentication**: None
* **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword123"
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "status": "success",
    "data": {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "expires_in": 3600
    }
  }
  ```
* **Validation Rules**: Email must be a valid format. Password must not be empty.

### 4.2. Bill Processing

#### POST `/api/v1/bills/upload`
Uploads a utility bill for OCR extraction and carbon calculation.

* **Method**: POST
* **Headers**: `Authorization: Bearer <token>`, `Content-Type: multipart/form-data`
* **Authentication**: Required
* **Request Body**: FormData containing file `bill_image` (PNG, JPEG, PDF)
* **Response (202 Accepted)**:
  ```json
  {
    "status": "success",
    "data": {
      "job_id": "job-12345",
      "message": "Bill uploaded successfully and is being processed."
    }
  }
  ```
* **Developer Note**: Due to API Gateway timeouts, processing should ideally be asynchronous. This endpoint returns a job ID to poll for status.

#### GET `/api/v1/bills/{bill_id}`
Retrieves extracted data for a specific bill.

* **Method**: GET
* **Authentication**: Required
* **Response (200 OK)**:
  ```json
  {
    "status": "success",
    "data": {
      "bill_id": "bill-123",
      "utility_type": "Electricity",
      "consumption": 1200,
      "unit": "kWh",
      "billing_period": "2023-10",
      "calculated_co2e": 450.5
    }
  }
  ```

### 4.3. Carbon Emissions

#### GET `/api/v1/emissions/summary`
Retrieves aggregated carbon emissions for the dashboard.

* **Method**: GET
* **Query Parameters**: `year` (optional), `month` (optional)
* **Authentication**: Required
* **Response (200 OK)**:
  ```json
  {
    "status": "success",
    "data": {
      "total_co2e": 5400.2,
      "scope_1": 1200.0,
      "scope_2": 3500.2,
      "scope_3": 700.0,
      "trend_percentage": -5.2
    }
  }
  ```

### 4.4. RAG Knowledge Engine

#### POST `/api/v1/chat/query`
Submits a compliance query to the RAG system.

* **Method**: POST
* **Headers**: `Authorization: Bearer <token>`, `Content-Type: application/json`
* **Authentication**: Required
* **Request Body**:
  ```json
  {
    "query": "How do I calculate emissions from employee commuting?"
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "status": "success",
    "data": {
      "answer": "According to the GHG Protocol Scope 3 Standard...",
      "sources": ["Scope3_Guidance.pdf - Page 45"]
    }
  }
  ```

## 5. Curl Examples

**Login:**
```bash
curl -X POST https://api.carbon-auditor.com/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@domain.com", "password":"password"}'
```

**Get Emissions:**
```bash
curl -X GET https://api.carbon-auditor.com/api/v1/emissions/summary \
     -H "Authorization: Bearer eyJhb..."
```

## 6. Status Codes

| Code | Description | Usage |
| :--- | :--- | :--- |
| 200 | OK | Successful GET, PUT, POST requests. |
| 201 | Created | Successful resource creation. |
| 202 | Accepted | Async task accepted (e.g., Bill Upload). |
| 400 | Bad Request | Validation errors, missing parameters. |
| 401 | Unauthorized | Missing or invalid JWT. |
| 403 | Forbidden | Insufficient permissions for the action. |
| 404 | Not Found | Resource does not exist. |
| 500 | Internal Server Error | Unhandled backend exception. |
