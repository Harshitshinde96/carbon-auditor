# Carbon-Auditor: Environment Variables

## 1. Purpose

This document catalogs all environment variables required to run the Carbon-Auditor platform across various environments (Local, Testing, Production). Strict adherence to this configuration ensures the application connects to the correct services securely.

## 2. Security Protocol

*   **Never commit `.env` files to version control.** Ensure `.env` is listed in `.gitignore`.
*   In local development, use a `.env` file placed in the root of the `backend/` directory.
*   In AWS production, these variables are injected into the Lambda function's configuration either directly or fetched dynamically from AWS Secrets Manager (for sensitive keys).

## 3. Global Variables

| Variable Name | Type | Description | Default / Example |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | String | Defines the current execution environment. Used to toggle debug modes or mock services. | `development` / `production` |
| `PROJECT_NAME` | String | Used by FastAPI for Swagger documentation titles. | `Carbon-Auditor API` |
| `AWS_REGION` | String | The AWS region where resources are deployed. | `us-east-1` |

## 4. Security & Authentication Variables

| Variable Name | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `JWT_SECRET` | String | A highly secure, random string used to sign JSON Web Tokens. Must be 32+ chars. | `8x!jK9z$2pL...` |
| `JWT_ALGORITHM` | String | The hashing algorithm used for JWTs. | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Integer | The lifespan of an authentication token. | `60` |

## 5. Third-Party API Keys (Secrets)

> [!CAUTION]
> In production, the Lambda function should ideally NOT have these as plain text environment variables. Instead, it should have the ARN of the AWS Secret Manager secret, and fetch these values at runtime.

| Variable Name | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `GEMINI_API_KEY` | String | Required for Document Understanding (Flash) and RAG generation. | `AIzaSyB...` |
| `QDRANT_API_KEY` | String | Required to authenticate with Qdrant Cloud Serverless. | `eyJhbG...` |
| `QDRANT_URL` | String | The host URL for the Qdrant Cloud cluster. | `https://xyz.us-east-1-0.aws.cloud.qdrant.io` |

## 6. AWS Resource Identifiers

These variables tell the backend which specific AWS resources to target, allowing easy switching between `dev` and `prod` infrastructure.

| Variable Name | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `S3_UPLOAD_BUCKET` | String | The bucket where raw utility bills are stored. | `carbon-dev-uploads` |
| `DYNAMO_TABLE_USERS` | String | Table name for user accounts. | `carbon-dev-users` |
| `DYNAMO_TABLE_BILLS` | String | Table name for processed bill metadata. | `carbon-dev-bills` |
| `DYNAMO_TABLE_EMISSIONS` | String | Table name for calculated emissions. | `carbon-dev-emissions` |

## 7. Local Testing Configuration (`.env.test`)

When running `pytest`, a separate `.env.test` file is used to ensure tests do not hit production databases.

```ini
ENVIRONMENT=testing
AWS_REGION=us-east-1
JWT_SECRET=test_secret_only
# Mock AWS resources will intercept these calls via the 'moto' library
S3_UPLOAD_BUCKET=mock-bucket
DYNAMO_TABLE_USERS=mock-users
GEMINI_API_KEY=mock-key
```
