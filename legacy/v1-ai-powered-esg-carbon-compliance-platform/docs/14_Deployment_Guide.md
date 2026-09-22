# Carbon-Auditor: Deployment Guide

## 1. Purpose

This document provides a rigorous, step-by-step guide for deploying the Carbon-Auditor platform to AWS. Following these instructions exactly will result in a fully operational production-grade environment.

## 2. Prerequisites

*   An active AWS Account.
*   AWS CLI installed and configured locally (`aws configure`).
*   Node.js (for frontend build if applicable) and Python 3.10+.
*   GitHub repository access.

## 3. Step-by-Step Infrastructure Deployment

### Step 1: Secure Secrets

We must first store the external API keys.

1.  Navigate to **AWS Secrets Manager** in the AWS Console.
2.  Click **Store a new secret**.
3.  Select **Other type of secret**.
4.  Add the following Key/Value pairs:
    *   `JWT_SECRET`: (Generate a long random string)
    *   `GEMINI_API_KEY`: (Your Google Gemini key)
    *   `QDRANT_API_KEY`: (Your Qdrant Cloud key)
5.  Name the secret: `carbon-dev-secrets`.
6.  Click **Next** and **Store**.

### Step 2: Create Storage Resources

#### S3 Buckets
1.  Navigate to **S3**.
2.  Create Bucket: `carbon-dev-storage` (Block all public access).
3.  Create Bucket: `carbon-dev-dashboard` (Block all public access).

#### DynamoDB Tables
1.  Navigate to **DynamoDB** -> **Tables** -> **Create table**.
2.  Table name: `carbon-dev-users`. Partition key: `user_id` (String). Capacity: On-Demand. Create.
3.  Repeat for `carbon-dev-bills` (PK: `company_id`, SK: `bill_id`).
4.  Repeat for `carbon-dev-emissions` (PK: `company_id`, SK: `emission_date`).

### Step 3: Configure IAM Role

1.  Navigate to **IAM** -> **Roles** -> **Create role**.
2.  Select **AWS Service** -> **Lambda**.
3.  Attach managed policy: `AWSLambdaBasicExecutionRole`.
4.  Create the role as `carbon-dev-lambda-execution-role`.
5.  Add an inline policy named `CarbonDevAccess` granting `dynamodb:*`, `s3:*`, and `secretsmanager:GetSecretValue` strictly restricted to resources starting with `carbon-dev-`.

### Step 4: Deploy the Backend (AWS Lambda & API Gateway)

> [!TIP]
> While manual deployment is detailed below, using GitHub Actions for CI/CD is the standard approach for this project.

1.  Package the FastAPI backend:
    ```bash
    cd backend
    pip install -r requirements.txt -t ./package
    cp -r app ./package
    cp main.py ./package
    cd package
    zip -r ../deployment.zip .
    ```
2.  Navigate to **AWS Lambda** -> **Create function**.
3.  Name: `carbon-dev-api`. Runtime: Python 3.10. Execution role: Use existing `carbon-dev-lambda-execution-role`.
4.  Upload the `deployment.zip` file.
5.  Under **Configuration** -> **General configuration**, set Memory to 1024 MB and Timeout to 29 seconds.
6.  Navigate to **API Gateway** -> Create **HTTP API**.
7.  Add integration: Select the Lambda function `carbon-dev-api`.
8.  Configure routes: Set a catch-all route `ANY /{proxy+}` to route all traffic to the Lambda.
9.  Deploy the API and note the Invoke URL.

### Step 5: Deploy the Frontend (S3 & CloudFront)

1.  Build the static frontend (if using a build tool, otherwise skip):
    ```bash
    cd frontend
    # If React/Vite: npm run build
    ```
2.  Upload the static files (or `dist` folder) to the `carbon-dev-dashboard` S3 bucket.
3.  Navigate to **CloudFront** -> **Create Distribution**.
4.  Origin domain: Select the `carbon-dev-dashboard` S3 bucket.
5.  Origin access: Select **Origin Access Control settings (recommended)** and create a new OAC.
6.  Viewer protocol policy: **Redirect HTTP to HTTPS**.
7.  Default root object: `index.html`.
8.  Create distribution.
9.  **Important**: Copy the generated S3 bucket policy from the CloudFront distribution settings and apply it to the `carbon-dev-dashboard` S3 bucket to allow CloudFront to read the files.

## 4. Verification

1.  Visit the CloudFront Distribution Domain Name in your browser. The login page should load.
2.  Open browser dev tools, verify that API requests are successfully hitting the API Gateway Invoke URL (ensure CORS is properly configured in FastAPI).
