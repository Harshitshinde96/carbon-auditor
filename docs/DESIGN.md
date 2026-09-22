# DESIGN.md — System Architecture & Blueprint

Authoritative for: folder structure, data models, and API contracts. `docs/PRD.md` is authoritative for *what* and *why*; this file is authoritative for *exact shape*. Where this file adds a detail not present in `PRD.md` (e.g. the `carbon-reports` table below), treat it as a valid, binding extension of PRD §11 — not a contradiction.

---

## 1. Monorepo Folder Topology

```
carbon-auditor/
├── AGENTS.md
├── docs/
│   ├── PRD.md
│   ├── TECH_STACK.md
│   ├── DESIGN.md
│   └── TASKS.md
├── docker-compose.yml
├── .gitignore
├── .editorconfig
├── pnpm-workspace.yaml
├── package.json                      # root — workspace scripts only, no app code
├── scripts/
│   ├── check.sh
│   └── deploy_ec2.sh
├── .github/
│   └── workflows/
│       ├── backend-ci.yml
│       └── frontend-ci.yml
├── legacy/
│   └── v1-ai-powered-esg-carbon-compliance-platform/   # verbatim copy of the v1 project folder — see TASKS.md Phase 1
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── .env.example
│   ├── main.py                        # FastAPI app instance (no Mangum)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── auth.py
│   │   │       ├── bills.py
│   │   │       ├── chat.py
│   │   │       ├── emissions.py
│   │   │       └── reports.py
│   │   ├── core/
│   │   │   ├── config.py              # Pydantic BaseSettings
│   │   │   ├── security.py            # JWT + bcrypt
│   │   │   └── exceptions.py          # CarbonBaseException hierarchy
│   │   ├── services/
│   │   │   ├── ocr_service.py         # adapted from legacy/ — see TASKS.md
│   │   │   ├── calc_engine.py         # deterministic, no legacy reuse
│   │   │   ├── rag_service.py         # adapted from legacy/ — see TASKS.md
│   │   │   └── report_service.py      # new
│   │   ├── repositories/
│   │   │   ├── dynamo_repo.py
│   │   │   └── s3_repo.py
│   │   ├── models/
│   │   │   ├── request.py
│   │   │   └── response.py
│   │   └── utils/
│   │       └── logging.py
│   ├── scripts/
│   │   └── ingest_knowledge.py        # RAG database population script
│   ├── data/
│   │   └── ghg_protocol_docs/         # Source PDFs/Excel for Qdrant ingestion
│   └── tests/
│       ├── unit/
│       │   ├── test_calc_engine.py
│       │   ├── test_ocr_service.py
│       │   ├── test_rag_service.py
│       │   ├── test_report_service.py
│       │   └── test_security.py
│       ├── integration/
│       │   ├── test_auth_api.py
│       │   ├── test_bills_api.py
│       │   ├── test_emissions_api.py
│       │   ├── test_chat_api.py
│       │   └── test_reports_api.py
│       └── golden/
│           ├── ocr_samples/           # 20 golden raw-OCR-text fixtures (PRD §19)
│           └── rag_eval_set.json      # 50 Q/A pairs (PRD §19)
└── frontend/
    ├── package.json
    ├── next.config.js
    ├── tailwind.config.ts
    ├── tsconfig.json
    ├── .env.example
    ├── app/
    │   ├── layout.tsx
    │   ├── globals.css
    │   ├── (auth)/
    │   │   └── login/page.tsx
    │   ├── dashboard/page.tsx
    │   ├── upload/page.tsx
    │   ├── bills/
    │   │   ├── page.tsx
    │   │   └── [id]/page.tsx
    │   ├── chat/page.tsx
    │   ├── reports/page.tsx
    │   └── settings/page.tsx
    ├── components/
    │   ├── ui/                        # shadcn/ui generated primitives
    │   ├── stat-card.tsx
    │   ├── scope-chart.tsx
    │   ├── bills-table.tsx
    │   ├── upload-dropzone.tsx
    │   └── chat-window.tsx
    ├── lib/
    │   ├── api-client.ts              # single fetch wrapper, 401 interceptor
    │   └── utils.ts
    ├── hooks/
    │   ├── use-bills.ts
    │   ├── use-emissions-summary.ts
    │   └── use-chat.ts
    └── tests/
        ├── unit/
        └── e2e/
```

---

## 2. Data Models (DynamoDB)

All tables use **on-demand capacity**. All timestamps are UTC ISO 8601 strings (PRD §28.5). All monetary/emissions numbers are stored pre-rounded to 2 decimal places (PRD §28.4).

### 2.1 `carbon-users`
| Attribute | Type | Notes |
|---|---|---|
| `user_id` (PK) | S | UUIDv4 |
| `email` | S | Unique — enforced at application layer via `EmailIndex` GSI lookup before insert |
| `password_hash` | S | bcrypt, cost 12 |
| `company_id` | S | One company per user in MVP |
| `role` | S | Enum: `"owner"` only in MVP |
| `created_at` | S | ISO 8601 |

**GSI:** `EmailIndex` — PK `email`. Used for login lookup and uniqueness checks.

### 2.2 `carbon-bills`
| Attribute | Type | Notes |
|---|---|---|
| `company_id` (PK) | S | |
| `bill_id` (SK) | S | UUIDv4 |
| `status` | S | Enum: `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`, `FAILED_OCR_QUALITY` |
| `s3_key` | S | Path to the raw uploaded file |
| `upload_date` | S | ISO 8601 |
| `utility_type` | S \| null | `ELECTRICITY` \| `NATURAL_GAS` \| `WATER` (PRD §5.1 — no others in MVP) |
| `consumption` | N \| null | |
| `unit` | S \| null | `kWh` \| `Therms` \| `Gallons` |
| `cost` | N \| null | In the company's configured currency (PRD §28.4) |
| `billing_period_start` | S \| null | `YYYY-MM-DD` |
| `billing_period_end` | S \| null | `YYYY-MM-DD` |
| `calculated_co2e_kg` | N \| null | |
| `scope` | S \| null | `SCOPE_1` \| `SCOPE_2` \| `SCOPE_3` |
| `factor_used` | N \| null | The exact factor value applied (PRD §13, for auditability) |
| `error_message` | S \| null | Populated only when `status` is a failure state |

**GSI:** `UploadDateIndex` — PK `company_id`, SK `upload_date`. Used for the paginated bill list (PRD §28.3) sorted descending.

### 2.3 `carbon-emissions`
| Attribute | Type | Notes |
|---|---|---|
| `company_id` (PK) | S | |
| `emission_date` (SK) | S | `YYYY-MM-DD` |
| `bill_id` | S | Traceability back to source bill |
| `scope` | S | `SCOPE_1` \| `SCOPE_2` \| `SCOPE_3` |
| `co2e_kg` | N | |

**GSI:** `ScopeIndex` — PK `company_id`, SK `scope`. Used for scope-based aggregation.

### 2.4 `carbon-settings`
| Attribute | Type | Notes |
|---|---|---|
| `company_id` (PK) | S | |
| `currency_code` | S | ISO 4217, set once at signup (PRD §28.4) |
| `reporting_year_start_month` | N | Default `1` |
| `created_at` | S | |

### 2.5 `carbon-reports` *(new table — extends PRD §11)*
The PRD's report flow (§16, §17) requires an async job-status pattern identical to bills, but no table was defined for it. This table closes that gap.

| Attribute | Type | Notes |
|---|---|---|
| `company_id` (PK) | S | |
| `report_id` (SK) | S | UUIDv4 |
| `status` | S | `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED` |
| `period_start` | S | `YYYY-MM-DD` |
| `period_end` | S | `YYYY-MM-DD` |
| `s3_key` | S \| null | Populated only once `status = COMPLETED` |
| `error_message` | S \| null | |
| `created_at` | S | |

---

## 3. API Contracts

Base path: `/api/v1`. Envelope per PRD §17:
- Success: `{ "status": "success", "data": { ... } }`
- Error: `{ "status": "error", "code": <int>, "message": "<string>", "details": [...] }`

### 3.1 `POST /auth/login`
**Request:**
```json
{ "email": "user@example.com", "password": "securepassword123" }
```
**200 OK:**
```json
{ "status": "success", "data": { "token": "<jwt>", "expires_in": 3600 } }
```
**401 Unauthorized** (bad credentials) / **400 Bad Request** (malformed email, per PRD §28.1).

### 3.2 `POST /bills/upload`
**Request:** `multipart/form-data`, field `bill_file` (PDF/PNG/JPEG/XLSX/CSV/DOCX/PPTX, <=15MB — PRD §28.2).
**202 Accepted:**
```json
{ "status": "success", "data": { "bill_id": "bill-uuid", "message": "Bill accepted for processing." } }
```
**400 Bad Request:** unsupported type or file >15MB — file must not reach S3 in this case.

### 3.3 `GET /bills/{bill_id}`
**200 OK (completed):**
```json
{
  "status": "success",
  "data": {
    "bill_id": "bill-uuid",
    "status": "COMPLETED",
    "upload_date": "2026-09-01T08:30:00Z",
    "extracted_data": {
      "utility_type": "ELECTRICITY",
      "consumption": 4500.5,
      "unit": "kWh",
      "cost": 520.75,
      "billing_period_start": "2026-08-01",
      "billing_period_end": "2026-08-31"
    },
    "emissions": { "calculated_co2e_kg": 1732.69, "scope": "SCOPE_2", "factor_used": 0.385 }
  }
}
```
**200 OK (failed):** `extracted_data`/`emissions` are `null`, `status` is `FAILED`/`FAILED_OCR_QUALITY`, `error_message` is non-null.
**404 Not Found:** unknown `bill_id`. **409 Conflict:** a reprocess request while `status = PROCESSING` (PRD §28.7).

### 3.4 `GET /bills` *(new — required by PRD §28.3)*
**Query params:** `limit` (default 20), `cursor` (opaque pagination token).
**200 OK:**
```json
{ "status": "success", "data": { "bills": [ /* array of bill summaries, same shape as 3.3 */ ], "next_cursor": "opaque-token-or-null" } }
```

### 3.5 `GET /emissions/summary`
**Query params:** `year` (optional), `month` (optional).
**200 OK:**
```json
{
  "status": "success",
  "data": {
    "period": "2026",
    "total_co2e_kg": 45000.5,
    "breakdown": { "SCOPE_1": 15000.0, "SCOPE_2": 25000.5, "SCOPE_3": 5000.0 },
    "monthly_trend": [ { "month": "2026-01", "total": 3500.0 } ]
  }
}
```

### 3.6 `POST /chat/query`
**Request:** `{ "query": "Does employee commuting fall under Scope 3?" }`
**200 OK:**
```json
{
  "status": "success",
  "data": {
    "answer": "Yes, employee commuting falls under Category 7 of Scope 3...",
    "sources": ["Scope3_Guidance.pdf - Page 32"],
    "confidence_score": 0.92
  }
}
```
`confidence_score` is defined exactly per PRD §28.6 — the top retrieval cosine similarity, rounded to 2 decimals, identical to the value checked against the 0.70 threshold.

### 3.7 `POST /reports/generate`
**Request:** `{ "period_start": "2026-01-01", "period_end": "2026-06-30" }`
**202 Accepted:** `{ "status": "success", "data": { "report_id": "report-uuid" } }`
**400 Bad Request:** `period_start >= period_end`, or range > 366 days (PRD §28.5).
**409 Conflict:** identical period already `PROCESSING` for this company (PRD §28.7).

### 3.8 `GET /reports/{report_id}`
**200 OK (completed):**
```json
{ "status": "success", "data": { "report_id": "report-uuid", "status": "COMPLETED", "download_url": "https://...signed-s3-url..." } }
```
**200 OK (pending/processing/failed):** `download_url` is `null`; `status` reflects current state; `error_message` populated on `FAILED`.

### 3.9 Standard Error Codes (unchanged from PRD §17/original API spec)
| Code | Meaning |
|---|---|
| 400 | Validation error |
| 401 | Missing/invalid/expired JWT |
| 403 | Authenticated but not authorized for this resource |
| 404 | Resource not found |
| 409 | Conflict (duplicate in-flight job, PRD §28.7) |
| 500 | Unhandled backend exception |

---

## 4. Key Flows (Sequence Reference)

### 4.1 Bill Upload → Emissions
`POST /bills/upload` → S3 write + DynamoDB `PENDING` row → `202` returned immediately → `BackgroundTask` runs `ocr_service` → `calc_engine` → DynamoDB updated to `COMPLETED`/`FAILED*` → frontend polls `GET /bills/{id}` via TanStack Query until a terminal `status`.

### 4.2 Report Generation
`POST /reports/generate` → validate date range → DynamoDB `PENDING` row in `carbon-reports` → `202` returned → `BackgroundTask` runs `report_service`: pull `carbon-bills`/`carbon-emissions` for the period → deterministic hotspot ranking → build a numbers-only prompt → Gemini Pro writes narrative sections → assemble PDF (WeasyPrint) → upload to S3 → DynamoDB updated to `COMPLETED` with `s3_key` → frontend polls `GET /reports/{id}` until `download_url` is present.

### 4.3 Compliance Chat
`POST /chat/query` → embed query (FastEmbed) → Qdrant top-5 similarity search → if top score < 0.70, return fallback (PRD §15/§29 US-4) → else build grounded prompt → Gemini Pro synthesis → return `answer` + `sources` + `confidence_score`.
