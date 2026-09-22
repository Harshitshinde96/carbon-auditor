# Carbon-Auditor: IAM and Security

## 1. Purpose

This document outlines the security posture of the Carbon-Auditor platform. It details AWS Identity and Access Management (IAM) configurations, encryption standards, and authentication mechanisms. Security is implemented following the Principle of Least Privilege.

## 2. Authentication & Authorization

### User Authentication
* **Method**: JSON Web Tokens (JWT).
* **Flow**: User logs in -> Backend verifies hash -> Generates JWT -> Frontend stores in `localStorage` or `HttpOnly Cookie`.
* **Authorization**: All secured API endpoints require the JWT in the `Authorization: Bearer <token>` header. FastAPI middleware decodes and validates the token expiration and signature.

### Third-Party API Keys
* API keys for **Gemini** and **Qdrant Cloud** must NEVER be hardcoded.
* They are stored securely in **AWS Secrets Manager** (`carbon-dev-secrets`) and fetched by the Lambda function at runtime (or injected as secure environment variables during CI/CD).

## 3. IAM Roles and Policies

### 3.1. API Execution Role
* **Role Name**: `carbon-dev-lambda-execution-role`
* **Attached To**: `carbon-dev-api` Lambda function.
* **Trust Relationship**:
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": { "Service": "lambda.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }]
  }
  ```
* **Policies**:
  1. `AWSLambdaBasicExecutionRole` (Managed) - For CloudWatch logging.
  2. `DynamoDBReadWriteAccess` (Inline) - Scoped specifically to `carbon-dev-*` tables.
  3. `S3ReadWriteAccess` (Inline) - Scoped to `carbon-dev-storage` bucket.
  4. `SecretsManagerRead` (Inline) - Scoped to `carbon-dev-secrets`.

**Least Privilege Explanation**: The Lambda function can only interact with DynamoDB tables and S3 buckets explicitly prefixed with `carbon-dev-`. It cannot delete tables or modify resources outside its operational scope.

### 3.2. GitHub Actions Deploy Role
* **Role Name**: `carbon-dev-github-deploy-role`
* **Purpose**: Used by CI/CD pipelines to deploy Lambda code and frontend assets.
* **Authentication**: Uses OpenID Connect (OIDC) with GitHub to avoid storing long-lived AWS access keys.
* **Permissions**: Allow updating Lambda code, S3 `PutObject` for the frontend bucket, and CloudFront invalidation.

## 4. Data Security

### 4.1. Encryption at Rest
* **DynamoDB**: Encrypted using AWS owned keys (Default SSE).
* **S3 Buckets**: SSE-S3 (Server-Side Encryption with Amazon S3 managed keys) enabled by default on `carbon-dev-storage`.

### 4.2. Encryption in Transit
* All data transferred between the user and CloudFront/API Gateway is encrypted using TLS 1.2/1.3 (HTTPS).
* Internal communication between AWS Lambda, DynamoDB, and Secrets Manager uses AWS secure internal networks.

## 5. S3 Bucket Security Policies

### Frontend Bucket (`carbon-dev-dashboard`)
* **Public Access**: Blocked.
* **Bucket Policy**: Only allows `s3:GetObject` from the specific CloudFront Origin Access Control (OAC).

### Data Bucket (`carbon-dev-storage`)
* **Public Access**: Blocked.
* **Bucket Policy**: No public access. Only the `carbon-dev-lambda-execution-role` can read/write objects.

## 6. Risks and Vulnerabilities

* **JWT Token Theft**: If tokens are stored in `localStorage`, they are vulnerable to XSS. *Mitigation: Ensure all user input in the dashboard is sanitized.*
* **Dependency Vulnerabilities**: Python packages (e.g., FastAPI, PaddleOCR) may have vulnerabilities. *Mitigation: Run `pip-audit` or Dependabot in GitHub Actions.*
