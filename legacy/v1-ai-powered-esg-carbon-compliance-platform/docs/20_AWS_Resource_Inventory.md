# Carbon-Auditor: AWS Resource Inventory

## 1. Purpose

This document serves as the master checklist and inventory of all AWS resources required to run the Carbon-Auditor platform. It is used by DevOps and cloud architects to track deployments, audit security boundaries, and monitor Free Tier limits.

## 2. Compute Services

| Resource ID / Name | AWS Service | Purpose | Notes / Limits |
| :--- | :--- | :--- | :--- |
| `carbon-dev-api` | AWS Lambda | Core backend running FastAPI. Handles OCR, Calc Engine, RAG. | 1024 MB Memory. 29s Timeout. |
| `carbon-dev-apigw` | API Gateway (HTTP) | Routes external traffic to the Lambda function. | Free Tier: 1M calls/month. |

## 3. Storage Services

| Resource ID / Name | AWS Service | Purpose | Notes / Limits |
| :--- | :--- | :--- | :--- |
| `carbon-dev-dashboard` | Amazon S3 | Hosts the compiled static frontend SPA assets (HTML/CSS/JS). | Block Public Access: ON (Accessed via CloudFront OAC). |
| `carbon-dev-storage` | Amazon S3 | Stores uploaded raw utility bills (PDFs/Images). | Default Encryption: SSE-S3. Lifecycle rules can be added later to archive old bills to Glacier. |

## 4. Database Services

| Resource ID / Name | AWS Service | Purpose | Notes / Limits |
| :--- | :--- | :--- | :--- |
| `carbon-dev-users` | Amazon DynamoDB | Stores user authentication data and roles. | Billing Mode: On-Demand. |
| `carbon-dev-bills` | Amazon DynamoDB | Stores structured JSON extracted from bills. | Billing Mode: On-Demand. |
| `carbon-dev-emissions`| Amazon DynamoDB | Stores calculated CO₂e records. | Billing Mode: On-Demand. Contains `ScopeIndex` GSI. |
| `carbon-dev-settings` | Amazon DynamoDB | Stores company-specific configurations. | Billing Mode: On-Demand. |

## 5. Security & Identity Services

| Resource ID / Name | AWS Service | Purpose | Notes / Limits |
| :--- | :--- | :--- | :--- |
| `carbon-dev-secrets` | Secrets Manager | Stores GEMINI_API_KEY, QDRANT_API_KEY, JWT_SECRET. | Cost: $0.40 per secret per month (Not strictly Free Tier, but minimal). |
| `carbon-dev-lambda-execution-role` | AWS IAM (Role) | Defines what the Lambda function is allowed to do. | Includes inline policy restricted to `carbon-dev-*` resources. |
| `carbon-dev-github-deploy-role` | AWS IAM (Role) | Allows GitHub Actions to deploy code. | Configured with OIDC trust relationship (No static keys). |

## 6. Networking & Content Delivery

| Resource ID / Name | AWS Service | Purpose | Notes / Limits |
| :--- | :--- | :--- | :--- |
| `carbon-dev-distribution` | Amazon CloudFront | Serves the frontend application globally with low latency. | Free Tier: 1 TB data transfer out/month. |

## 7. Monitoring & Logging

| Resource ID / Name | AWS Service | Purpose | Notes / Limits |
| :--- | :--- | :--- | :--- |
| `/aws/lambda/carbon-dev-api` | CloudWatch Logs | Centralized log storage for the backend Lambda function. | Ensure retention policy is set to 14 or 30 days to prevent infinite storage costs. |

## 8. Third-Party Integrations (External to AWS)

For completeness, these external resources form part of the infrastructure ecosystem:

| Resource Name | Provider | Purpose |
| :--- | :--- | :--- |
| `Carbon-Auditor Knowledge Base` | Qdrant Cloud | Vector Database hosting GHG protocol embeddings. (Serverless Free Tier cluster). |
| `Gemini Flash Model` | Google AI Studio | Document understanding and JSON extraction. |
| `Gemini Pro Model` | Google AI Studio | RAG text synthesis and compliance answering. |
