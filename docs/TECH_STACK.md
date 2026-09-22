# TECH_STACK.md — Environment & Commands Contract

This file is the **single source of truth for environment, tooling, and commands**. `docs/PRD.md` defines *what* to build; `docs/DESIGN.md` defines *how it's structured*; this file defines *exactly what to type into a terminal* to install, run, lint, and test it. If a command here fails or doesn't exist, that is a blocker — do not improvise a substitute command; halt per `AGENTS.md`.

---

## 1. Repository Type

A single Git monorepo containing a Python backend and a TypeScript/Next.js frontend, managed as a **pnpm workspace** at the root (for the JS/TS side only — the Python backend uses its own virtual environment and is not part of the pnpm workspace graph).

## 2. Exact Versions (Pinned)

| Tool | Version | Notes |
|---|---|---|
| Python | `3.12.x` | Backend runtime |
| Node.js | `20.x` (LTS) | Frontend runtime |
| pnpm | `9.x` | `corepack enable && corepack prepare pnpm@9 --activate` |
| Docker | `24.x`+ | Required for local full-stack dev and deployment |
| Docker Compose | `v2` (the `docker compose` subcommand, not the old `docker-compose` binary) |

## 3. Backend Dependencies (`backend/requirements.txt`)

```
fastapi==0.115.*
uvicorn[standard]==0.30.*
gunicorn==22.*
pydantic==2.*
pydantic-settings==2.*
boto3==1.34.*
python-jose[cryptography]==3.3.*
passlib[bcrypt]==1.7.*
bcrypt==3.2.2
python-multipart==0.0.*
paddleocr==2.9.*
paddlepaddle==3.0.*
pdf2image==1.17.*
google-generativeai==0.8.*
fastembed==0.3.*
qdrant-client==1.12.*
weasyprint==62.*
python-dotenv==1.*
```

## 4. Backend Dev Dependencies (`backend/requirements-dev.txt`)

```
pytest==8.*
pytest-cov==5.*
pytest-asyncio==0.23.*
moto[dynamodb,s3]==5.*
httpx==0.27.*
black==24.*
flake8==7.*
mypy==1.*
bandit==1.7.*
```

## 5. Frontend Dependencies (high-level — exact versions locked by `pnpm-lock.yaml` once generated)

- `next` (14.x, App Router), `react`, `react-dom`, `typescript`
- `tailwindcss`, `postcss`, `autoprefixer`
- `@radix-ui/*` + shadcn/ui generated components
- `@tanstack/react-query`
- `react-hook-form`, `zod`, `@hookform/resolvers`
- `recharts`
- `next/font` (built into Next.js — used to load Geist)
- Dev: `eslint`, `eslint-config-next`, `prettier`, `jest`, `@testing-library/react`, `@playwright/test`

## 6. One-Time Setup

```bash
# Clone and enter repo
git clone <repo-url> carbon-auditor && cd carbon-auditor

# Frontend workspace
corepack enable
corepack prepare pnpm@9 --activate
pnpm install

# Backend virtual environment
cd backend
python3.11 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
cd ..

# Environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# Populate RAG Database (Requires QDRANT_URL and QDRANT_API_KEY in .env)
cd backend
source .venv/bin/activate
python scripts/ingest_knowledge.py
cd ..
```

## 7. Local Development

```bash
# Full stack, containerized (preferred — matches production runtime)
docker compose up --build

# Backend only, without Docker
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Frontend only
cd frontend
pnpm dev
```

`docker-compose.yml` must include three services for local dev: `backend` (FastAPI), `frontend` (Next.js), and `dynamodb-local` (`amazon/dynamodb-local` image, for local testing against a real DynamoDB API without touching AWS). S3 access in local dev talks to a real (free-tier) S3 bucket — there is no practical local S3 substitute worth the setup cost at this project's size, so `backend/.env` must point at a real (dev) bucket even for local runs.

## 8. Linting & Formatting

```bash
# Backend — check (CI mode, non-mutating)
black --check backend/app backend/tests
flake8 backend/app backend/tests
mypy backend/app

# Backend — auto-fix
black backend/app backend/tests

# Frontend — check
pnpm --filter frontend lint

# Frontend — auto-fix
pnpm --filter frontend format
```

## 9. Testing (All Automated — No Manual Test Steps Anywhere in This Project)

```bash
# Backend — full suite with coverage gate (fails build if < 80%)
cd backend
pytest --cov=app --cov-report=term-missing --cov-fail-under=80

# Backend — calc engine only, 100% coverage gate (non-negotiable per PRD §13/§19)
pytest tests/unit/test_calc_engine.py --cov=app.services.calc_engine --cov-report=term-missing --cov-fail-under=100

# Backend — security scan
bandit -r backend/app

# Frontend — unit/component tests
pnpm --filter frontend test

# Frontend — E2E (requires backend + frontend running; docker compose up first)
pnpm --filter frontend test:e2e
```

## 10. Single Command: "Am I Green?" (Run Before Marking Any Task Complete)

Create `scripts/check.sh` in Phase 1 (see `TASKS.md`) with this exact content, and always run it — never mark a `TASKS.md` checkbox complete without a clean run of this script:

```bash
#!/usr/bin/env bash
set -e
echo "== Backend lint =="
black --check backend/app backend/tests
flake8 backend/app backend/tests
mypy backend/app
echo "== Backend tests =="
cd backend && pytest --cov=app --cov-report=term-missing --cov-fail-under=80 && cd ..
echo "== Frontend lint =="
pnpm --filter frontend lint
echo "== Frontend tests =="
pnpm --filter frontend test
echo "ALL GREEN"
```

## 11. Build & Deploy

```bash
# Frontend production build (Vercel runs this automatically on push — this is for local verification only)
pnpm --filter frontend build

# Backend Docker image
docker build -t carbon-auditor-backend:latest ./backend

# Deploy to EC2 (see scripts/deploy_ec2.sh, created in the Deployment phase of TASKS.md)
./scripts/deploy_ec2.sh
```

Frontend deploys automatically via Vercel's Git integration — no manual deploy command exists or should be created for it.

## 12. Disallowed Packages / Tools

An agent must **never** install or introduce any of the following, regardless of how convenient they seem mid-task. If a task appears to require one of these, stop and flag it per `AGENTS.md` rather than installing it.

| Disallowed | Reason |
|---|---|
| `mangum` | Lambda-specific — this project is no longer Lambda-hosted (PRD §6.1) |
| `serverless` / `aws-sam-cli` | No Lambda-based deployment in this project |
| `flask`, `django` | FastAPI is the only backend framework (PRD §8.2) |
| `sqlalchemy`, `psycopg2`, any SQL/ORM package | No relational database — DynamoDB only (PRD §8.3, §11) |
| `pymongo`, any MongoDB client | Not part of the stack |
| `moment` | Use native `Intl`/`date-fns` if a helper is truly needed |
| `redux`, `mobx` | TanStack Query + local component state is the standard (PRD §8.1); do not introduce a global state library |
| `axios` | Use the native `fetch` API wrapped by the shared API client (`frontend/lib/api-client.ts`) — do not add a second HTTP client |
| `bootstrap`, `material-ui`/`@mui`, `chakra-ui`, `styled-components`, `emotion` | Tailwind CSS + shadcn/ui is the only UI system (PRD §8.1, §10) |
| `jquery` | Not compatible with the React/Next.js architecture |
| `create-react-app` | Next.js is the only frontend framework/build tool |
| Any vector DB client other than `qdrant-client` (e.g. `pinecone-client`, `weaviate-client`, `chromadb`) | Qdrant Cloud is the only vector DB (PRD §8.3, §15) |
| Any OCR library other than `paddleocr` (e.g. `pytesseract`, `easyocr`) | PaddleOCR is the specified OCR engine (PRD §8.4, §14) |
| Any LLM SDK other than `google-generativeai` (e.g. `openai`, `anthropic`) | Gemini is the specified model provider throughout the PRD |
| `boto3` alternatives (e.g. `aioboto3` unless a specific async need is documented in `DESIGN.md`) | Keep AWS access consistent and synchronous unless stated otherwise |
| Any `@aws-sdk/*` package in the **frontend** | The frontend never talks to AWS directly — all AWS access is mediated by the backend API (security boundary, PRD §12) |
| `next-auth` or any third-party auth library | Custom JWT auth per PRD §8.5/§28.1 is the only auth mechanism in MVP |
### Coding Standards
- **Modular Architecture:** Write modular code for everything built. Break large files into smaller components, services, and utilities. Do not cram logic into a single file.
