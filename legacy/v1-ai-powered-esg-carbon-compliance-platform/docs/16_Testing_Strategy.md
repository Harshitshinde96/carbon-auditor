# Carbon-Auditor: Testing Strategy

## 1. Purpose

This document outlines the testing methodology to ensure the reliability, accuracy, and security of the Carbon-Auditor platform. Because this software deals with compliance and deterministic math, rigorous testing is non-negotiable.

## 2. Test Pyramid

We adhere to the standard testing pyramid, prioritizing fast, isolated tests over slow, brittle end-to-end tests.

1.  **Unit Tests (70%)**: Test individual functions and classes in isolation.
2.  **Integration Tests (20%)**: Test interactions between services and databases (e.g., API to DynamoDB).
3.  **End-to-End (E2E) Tests (10%)**: Test complete user workflows through the UI.

## 3. Backend Testing (Python)

**Framework**: `pytest`

### 3.1. Unit Testing
*   **Carbon Calculation Engine**: This is the most critical part of the system. We must have 100% test coverage for `calc_engine.py`. Tests must cover all utility types, edge cases (zero, negative numbers), and floating-point rounding validations.
*   **Mocking**: Use `unittest.mock` to stub out external dependencies (AWS S3, DynamoDB, Gemini API) during unit tests. Services must not make real network calls during unit testing.

### 3.2. Integration Testing
*   Use `moto` (Mock AWS Services) to spin up in-memory versions of DynamoDB and S3 during the test suite execution.
*   Use FastAPI's `TestClient` to send requests to the API endpoints and assert the responses, verifying that the router, service, and mocked database layer work together correctly.

## 4. Frontend Testing

**Frameworks**: `Jest` (Logic), `Testing Library` (Components/DOM), `Playwright` (E2E).

### 4.1. Unit & Component Tests
*   Test utility functions (e.g., date formatting, data transformation).
*   If using React, test that components render correctly given specific props.

### 4.2. E2E Testing
*   Use Playwright to script automated browser tests for core user journeys:
    *   User Login -> Success.
    *   User uploads bill -> Dashboard updates with new bill status.
    *   User asks a question in Chat -> Receives a response.

## 5. AI/LLM Specific Testing

Testing stochastic systems (LLMs) requires a different approach.

*   **Prompt Regression Testing**: Maintain a test suite of 20 diverse "Golden" raw OCR texts (representing various utility bills). Assert that the Pydantic schema validation passes for the Gemini Flash output on all 20 texts whenever the system prompt is modified.
*   **RAG Evaluation**: Create a dataset of 50 compliance questions and their expected answers. Automatically evaluate the RAG pipeline's retrieval accuracy (did it fetch the right document?) and response quality.

## 6. Continuous Integration (CI)

All tests are enforced via GitHub Actions.

*   **On Push/PR**: 
    *   Run Linter (`black`, `flake8`).
    *   Run `pytest` (Backend Unit & Integration).
    *   Run `npm test` (Frontend Unit).
*   **Gatekeeper**: A Pull Request cannot be merged if any tests fail or if test coverage drops below 80%.

## 7. Security and Load Testing (Pre-Production)

*   **SAST**: Integrate a Static Application Security Testing tool (e.g., Bandit for Python) into the CI pipeline to scan for hardcoded secrets or common vulnerabilities.
*   **Load Testing**: Before a major release, use a tool like `Artillery` or `Locust` to simulate 100 concurrent users hitting the API Gateway to verify that DynamoDB on-demand scaling and Lambda concurrency handle the load without throwing 500/502 errors.
