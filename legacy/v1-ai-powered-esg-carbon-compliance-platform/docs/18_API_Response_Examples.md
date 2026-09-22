# Carbon-Auditor: API Response Examples

## 1. Purpose

This document provides extensive examples of API requests and responses for the Carbon-Auditor platform. These examples serve as a reference for frontend developers and external integrators to understand the exact payload structures, including edge cases and errors.

## 2. Authentication API (`/api/v1/auth`)

### 2.1. Successful Login
**Request:**
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "auditor@enterprise.com",
  "password": "securepassword123"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYXVkaXRvci11dWlkIiwiaWF0IjoxNjk3MzQxNDAwLCJleHAiOjE2OTczNDUwMDB9.xyz...",
    "expires_in": 3600,
    "user": {
      "id": "auditor-uuid",
      "email": "auditor@enterprise.com",
      "role": "auditor"
    }
  }
}
```

### 2.2. Failed Login (Invalid Credentials)
**Response (401 Unauthorized):**
```json
{
  "status": "error",
  "code": 401,
  "message": "Invalid email or password",
  "details": []
}
```

## 3. Bill Processing API (`/api/v1/bills`)

### 3.1. Successful File Upload (Async Accepted)
**Request:**
```http
POST /api/v1/bills/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

(file: bill_image.pdf attached)
```

**Response (202 Accepted):**
```json
{
  "status": "success",
  "data": {
    "job_id": "job-987654321",
    "message": "File accepted for processing. Check status using the job ID.",
    "estimated_completion_seconds": 15
  }
}
```

### 3.2. Fetch Processed Bill Data (Success)
**Request:**
```http
GET /api/v1/bills/bill-abc-123
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "bill_id": "bill-abc-123",
    "status": "COMPLETED",
    "upload_date": "2023-10-15T08:30:00Z",
    "extracted_data": {
      "utility_type": "ELECTRICITY",
      "consumption": 4500.5,
      "unit": "kWh",
      "cost": 520.75,
      "billing_period_start": "2023-09-01",
      "billing_period_end": "2023-09-30"
    },
    "emissions": {
      "calculated_co2e_kg": 1732.69,
      "scope": "SCOPE_2",
      "factor_used": 0.385
    }
  }
}
```

### 3.3. Fetch Processed Bill Data (OCR Failed)
**Response (200 OK - Note status field):**
```json
{
  "status": "success",
  "data": {
    "bill_id": "bill-def-456",
    "status": "FAILED",
    "error_message": "Document quality too low for OCR extraction.",
    "extracted_data": null,
    "emissions": null
  }
}
```

## 4. Emissions Dashboard API (`/api/v1/emissions`)

### 4.1. Get Dashboard Summary
**Request:**
```http
GET /api/v1/emissions/summary?year=2023
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "period": "2023",
    "total_co2e_kg": 45000.5,
    "breakdown": {
      "SCOPE_1": 15000.0,
      "SCOPE_2": 25000.5,
      "SCOPE_3": 5000.0
    },
    "monthly_trend": [
      {"month": "2023-01", "total": 3500.0},
      {"month": "2023-02", "total": 3600.0},
      {"month": "2023-09", "total": 4100.5}
    ]
  }
}
```

## 5. RAG Chat API (`/api/v1/chat`)

### 5.1. Successful Query
**Request:**
```http
POST /api/v1/chat/query
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "Does employee commuting fall under Scope 3?"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "answer": "Yes, according to the Corporate Value Chain (Scope 3) Accounting and Reporting Standard, employee commuting is classified under Category 7 of Scope 3 emissions. This includes transportation of employees between their homes and worksites.",
    "sources": [
      "Scope3_Guidance.pdf - Page 32"
    ],
    "confidence_score": 0.92
  }
}
```

### 5.2. Out of Context Query
**Request:**
```http
POST /api/v1/chat/query
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "What is the capital of France?"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "answer": "I cannot find the answer to this question in the provided GHG guidelines. My expertise is strictly limited to ESG and Carbon Compliance.",
    "sources": [],
    "confidence_score": 0.12
  }
}
```
