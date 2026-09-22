# Carbon-Auditor: Project Overview

## 1. Purpose

The Carbon-Auditor is an **Automated ESG & Carbon Compliance Engine** designed to automate utility bill processing, carbon footprint calculation, ESG compliance guidance, AI-assisted carbon auditing, and energy analytics for businesses. This platform empowers organizations to seamlessly track, analyze, and optimize their carbon emissions while adhering to global ESG standards.

## 2. Overview

In the modern enterprise landscape, ESG reporting has evolved from an optional transparency metric into a strict compliance requirement. Carbon-Auditor eliminates the manual overhead of data collection and emission calculations. The platform extracts consumption data directly from utility bills using Optical Character Recognition (OCR), processes the information through a deterministic carbon calculation engine, and displays actionable insights via an intuitive dashboard.

> [!NOTE]
> The AI capabilities (RAG Knowledge Engine and Gemini Flash) are strictly used for data extraction and regulatory query assistance. All emission calculations are deterministic and adhere to GHG Protocol standards.

## 3. High-Level System Components

The platform consists of five major integrated systems:

1. **On-Demand Bill Processing**: Manages the upload, OCR data extraction (PaddleOCR + Gemini Flash), and structured storage of utility bills.
2. **Carbon Calculation Engine**: A deterministic business logic layer responsible for scope classification, emission factor application, and CO₂e aggregations.
3. **RAG Knowledge Engine**: Provides an interactive querying system over GHG Protocol PDFs and Excel guidelines using FastEmbed, Qdrant Cloud, and Gemini.
4. **Dashboard**: A React-based (or vanilla JS SPA) frontend offering visual analytics, reporting, and direct user interaction.
5. **Automation System**: Handles the scheduled generation of reports, notifications via Telegram, and automated Google Sheets synchronization (documented but maintained by a separate team).

## 4. Architecture Principles

Our architecture adheres to the following principles:

* **Production-Grade Scalability**: Designed using a microservices-inspired Serverless architecture to handle enterprise-level loads.
* **Cost Efficiency**: Leveraging AWS Free Tier services (DynamoDB over RDS, Lambda, S3, CloudFront) to maintain zero to near-zero development costs.
* **Separation of Concerns**: Strict boundary enforcement between Controllers, Services, and Repositories. No business logic resides in controllers.
* **RESTful Standards**: All APIs are versioned under `/api/v1/` and follow rigorous REST design principles.
* **Naming Conventions**: Strict adherence to the `carbon-dev-*` naming pattern for all AWS resources (e.g., `carbon-dev-api`, `carbon-dev-users`).

## 5. Technology Stack Summary

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | HTML, CSS, JavaScript (Static SPA hosted on Amazon S3 + CloudFront) |
| **Backend** | Python, FastAPI, Mangum, AWS Lambda, API Gateway |
| **Storage & Database** | Amazon S3, Amazon DynamoDB |
| **Authentication & Security** | JWT, AWS Secrets Manager |
| **AI & OCR** | PaddleOCR, Gemini Flash (Document Understanding), Gemini (LLM) |
| **Vector Database** | Qdrant Cloud Serverless (BAAI/bge-small-en-v1.5 embeddings via FastEmbed) |
| **DevOps & CI/CD** | GitHub, GitHub Actions, AWS CloudWatch |

## 6. Target Audience

* **Sustainability Officers**: For tracking and reporting carbon compliance.
* **Facility Managers**: For analyzing utility consumption and operational efficiency.
* **Corporate Auditors**: For verifying the deterministic calculations against standard ESG guidelines.

## 7. Risks and Assumptions

### Assumptions
* The AWS Free Tier limits will not be exceeded during the standard development and testing lifecycle.
* Utility bills uploaded will be in common formats (PDF, PNG, JPEG) and have legible typography for OCR.
* The GHG protocol guidelines remain relatively static for the duration of the current calculation engine version.

### Risks
* **OCR Inaccuracies**: Poor quality scans might lead to faulty data extraction. *Mitigation: Implement human-in-the-loop verification in the dashboard.*
* **Cold Starts**: Serverless functions (AWS Lambda) interacting with FastAPI and heavy ML models (PaddleOCR) might experience latency during cold starts. *Mitigation: Proper memory allocation and provisioned concurrency in production.*

## 8. Future Production Upgrade Notes
* **Database**: Migration from DynamoDB to Amazon Aurora PostgreSQL (RDS) if relational query complexity increases.
* **Message Broker**: Introduction of Amazon SQS/EventBridge for asynchronous decoupled processing between the OCR pipeline and the Calculation Engine.
* **Compute**: Transition from AWS Lambda to Amazon ECS (Fargate) for long-running OCR and AI inference tasks.
