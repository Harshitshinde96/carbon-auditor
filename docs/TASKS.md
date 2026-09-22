# TASKS.md — Atomic Implementation Roadmap

**How to invoke this roadmap:** you do not need to prompt the agent separately for every task. Naming a phase or range (e.g. *"start work on Phase 0 and Phase 1"*, *"do everything through Phase 5"*, *"run the whole roadmap"*) puts the agent in **Batch Mode** per `AGENTS.md` — it will work through every task in that range on its own, running every test, fixing failures itself where possible, and only stopping for a genuine blocker (see `AGENTS.md`'s Stop Conditions). Naming no scope at all puts it in single-task mode, one checkbox at a time. Either way, every task below still runs its own test-first cycle — batch mode changes how much you have to ask for, never how carefully each task is verified.

**Rules for every task below:**
1. Execute unchecked tasks in order, top to bottom, phase by phase. Do not skip ahead.
2. Every task that touches code follows **test-first**: write/adjust the test → implement the minimum code to pass it → run the exact command listed → confirm a green result → check the box. A task with no test command listed is a non-code task (setup, copy, config) — still confirm its own explicit verification step before checking it off.
3. Never check a box on a failing or skipped test.
4. Every phase ends with a **Phase Gate** task that re-runs the relevant automated checks for everything built so far in that phase. A phase is not complete — and the next phase must not start — until its gate is green. This is what makes the whole roadmap safe to run unattended in Batch Mode: nothing moves forward on a red build.
5. If a task's prerequisites (a file, a folder, a prior task) are missing, stop and follow the Stop Conditions in `AGENTS.md` — do not improvise around a missing dependency.

---

## Phase 0 — Monorepo Scaffolding

- [x] **0.1 — Initialize the monorepo root.** Create the folder structure exactly as specified in `docs/DESIGN.md` §1 (every directory listed, even if empty — use `.gitkeep` placeholders where a folder has no file yet). Initialize git (`git init` if not already a repo). Create root `.gitignore` covering: `.venv/`, `__pycache__/`, `node_modules/`, `.next/`, `*.env`, `.env.local`, `dist/`, `.pytest_cache/`, `.mypy_cache/`, `htmlcov/`.
  **Verify:** `find . -maxdepth 2 -type d` output matches the tree in `DESIGN.md` §1.

- [x] **0.2 — Copy `AGENTS.md` and the `docs/` folder into the new project root.** Copy `AGENTS.md`, `docs/PRD.md`, `docs/TECH_STACK.md`, `docs/DESIGN.md`, and this file (`docs/TASKS.md`) from wherever they were generated/staged into the new monorepo's root and `docs/` folder respectively, so the repo is self-describing from its first commit.
  **Verify:** `ls AGENTS.md docs/PRD.md docs/TECH_STACK.md docs/DESIGN.md docs/TASKS.md` — all five resolve with no "No such file" error.

- [x] **0.3 — Copy the v1 reference project into `legacy/`.** Copy the entire existing **"AI-powered ESG and Carbon Compliance Platform"** folder (the v1 build referenced in `PRD.md` §6.3) verbatim into `legacy/v1-ai-powered-esg-carbon-compliance-platform/` in the new repo. Do not modify anything inside it yet — this phase is a straight copy so the reference implementation (including the existing OCR and RAG service code) is preserved and available for Phases 5 and 6 below.
  **Verify:** `ls legacy/v1-ai-powered-esg-carbon-compliance-platform/` is non-empty and visibly contains the original backend source (e.g. an `app/services/` or equivalent path with `ocr_service.py`/`rag_service.py`-type files).

- [x] **0.4 — Root workspace files.** Create `pnpm-workspace.yaml` (packages: `frontend`), root `package.json` (workspace scripts only, no dependencies), `.editorconfig` (2-space JS/TS, 4-space Python via `[*.py] indent_size = 4`).
  **Verify:** `pnpm install` at the repo root completes with no errors (frontend `package.json` must exist first — see Phase 8).

- [x] **0.5 — `scripts/check.sh`.** Create the file exactly as specified in `TECH_STACK.md` §10. `chmod +x scripts/check.sh`.
  **Verify:** `./scripts/check.sh` runs (it will fail at this point since no backend/frontend code exists yet — that failure is expected and acceptable only for this one verification; do not check this box until it at least *executes* without a "command not found"/permission error).

- [x] **0.6 — CI workflow skeletons.** Create `.github/workflows/backend-ci.yml` and `.github/workflows/frontend-ci.yml`, each running the equivalent lint+test commands from `TECH_STACK.md` §8–9 on every push/PR.
  **Verify:** YAML is valid (`yamllint` or equivalent) and each workflow references the exact commands from `TECH_STACK.md` — no invented commands.

- [x] **PHASE 0 GATE.** Confirm: the full folder tree matches `DESIGN.md` §1; `AGENTS.md` + all four `docs/*.md` files are present in the new repo; `legacy/v1-ai-powered-esg-carbon-compliance-platform/` is populated; `pnpm install` succeeds at the root; `scripts/check.sh` is executable. Commit with message `chore: scaffold monorepo (Phase 0)`. Do not start Phase 1 until every item in this list is true.

---

## Phase 1 — Backend Core Foundation

- [x] **1.1 — Backend project skeleton.** Create `backend/main.py`, `backend/requirements.txt`, `backend/requirements-dev.txt` (contents exactly per `TECH_STACK.md` §3–4), `backend/Dockerfile`, `backend/.env.example` (all variables from `PRD.md` §21). Set up the venv per `TECH_STACK.md` §6.
  **Verify:** `pip install -r backend/requirements.txt -r backend/requirements-dev.txt` completes with no errors.

- [x] **1.2 — `app/core/config.py`.** Write a failing test first (`backend/tests/unit/test_config.py`) asserting that `Settings()` loads `JWT_SECRET`, `GEMINI_API_KEY`, `QDRANT_API_KEY`, `QDRANT_URL`, `S3_UPLOAD_BUCKET`, `DYNAMO_TABLE_*`, and `AWS_REGION` from environment variables and raises a validation error if a required one is missing. Implement `Settings(BaseSettings)` to satisfy it.
  **Run:** `pytest backend/tests/unit/test_config.py -v` → confirm pass.

- [x] **1.3 — `app/core/exceptions.py`.** Write tests asserting `CarbonBaseException` and each subclass (`AuthenticationError` 401, `AuthorizationError` 403, `ResourceNotFoundError` 404, `ValidationProcessingError` 422, `OCRProcessingError` 500, `InvalidConsumptionError`, `UnsupportedUtilityTypeError`, `UnitMismatchError`) carry the correct `status_code`, `message`, and optional `details`. Implement the hierarchy.
  **Run:** `pytest backend/tests/unit/test_exceptions.py -v` → confirm pass.

- [x] **1.4 — Global exception handler in `main.py`.** Write an integration test (`backend/tests/integration/test_error_envelope.py`) that hits a temporary route raising each custom exception and asserts the JSON envelope matches `DESIGN.md` §3 exactly. Implement the handler.
  **Run:** `pytest backend/tests/integration/test_error_envelope.py -v` → confirm pass.

- [x] **1.5 — `app/core/security.py` — password hashing.** Write tests: hashing a password with `passlib`/bcrypt (cost 12, per `PRD.md` §28.1) and verifying it round-trips; verifying a wrong password fails. Implement `hash_password()`/`verify_password()`.
  **Run:** `pytest backend/tests/unit/test_security.py -v` → confirm pass.

- [x] **1.6 — `app/core/security.py` — JWT issuance/validation.** Write tests: a token issued with a given `user_id`/`company_id` decodes back to the same claims; an expired token (mock `ACCESS_TOKEN_EXPIRE_MINUTES` in the past) fails validation; a tampered token fails validation. Implement `create_access_token()`/`decode_access_token()`.
  **Run:** `pytest backend/tests/unit/test_security.py -v` → confirm pass, full file green.

- [x] **1.7 — `app/repositories/dynamo_repo.py`.** Using `moto`, write tests for generic `put_item`/`get_item`/`query` helper functions against a mocked `carbon-bills` table (create the table schema in the test fixture per `DESIGN.md` §2.2, including the `UploadDateIndex` GSI). Implement the repository.
  **Run:** `pytest backend/tests/unit/test_dynamo_repo.py -v` → confirm pass.

- [x] **1.8 — `app/repositories/s3_repo.py`.** Using `moto`, write tests for `upload_file()`, `get_signed_url()`, and `download_file()` against a mocked bucket. Implement the repository.
  **Run:** `pytest backend/tests/unit/test_s3_repo.py -v` → confirm pass.

- [x] **PHASE 1 GATE.** Run `cd backend && pytest --cov=app --cov-report=term-missing -v` (no coverage-fail-under yet — feature set is incomplete — but confirm **zero failing tests** among everything written so far) and `black --check backend/app backend/tests && flake8 backend/app backend/tests && mypy backend/app`. All must be clean. Commit with message `feat: backend core foundation (Phase 1)`. Do not start Phase 2 until this is green.

---

## Phase 2 — Carbon Calculation Engine (Non-Negotiable Core — 100% Coverage Gate)

- [x] **2.1 — Golden test cases.** Write `backend/tests/unit/test_calc_engine.py` covering, per `PRD.md` §13/§29 (US-6): each of the 3 utility types with a normal positive value; a zero-consumption edge case; a negative-consumption case (expect `InvalidConsumptionError`); an unrecognized `utility_type` (expect `UnsupportedUtilityTypeError`); a unit mismatch case (expect `UnitMismatchError`); a rounding case that exercises the "round to 2 decimals" rule with a value that would otherwise have more precision.
  **Run:** `pytest backend/tests/unit/test_calc_engine.py -v` → confirm it currently **fails** (no implementation exists yet) — this failing-first state is expected and required before 2.2.

- [x] **2.2 — Implement `app/services/calc_engine.py`.** Pure, deterministic Python. No AI/LLM calls of any kind inside this file — this is enforced by the test suite never mocking an LLM here (if a test in this file ever needs to mock Gemini/PaddleOCR, that is a sign the logic is in the wrong file). Implement the formula and error handling from `PRD.md` §13 and `DESIGN.md`.
  **Run:** `pytest tests/unit/test_calc_engine.py --cov=app.services.calc_engine --cov-report=term-missing --cov-fail-under=100` (from `backend/`) → confirm **100% coverage and all tests pass**. Do not proceed past this task at anything less than 100%.

- [x] **PHASE 2 GATE.** Re-run the exact command from 2.2 one more time from a clean state (`git stash` any uncommitted noise first if needed) to confirm the 100% gate is stable, not a fluke of test order. Commit with message `feat: deterministic carbon calculation engine, 100% coverage (Phase 2)`. Do not start Phase 3 until this is green.

---

## Phase 3 — OCR Service (Adapted From Legacy v1)

- [x] **3.1 — Copy the legacy OCR implementation.** Copy `ocr_service.py` (and any directly-related prompt/schema files it imports) from `legacy/v1-ai-powered-esg-carbon-compliance-platform/` into `backend/app/services/ocr_service.py`, unmodified, as the starting point (per `PRD.md` §6.3 — do not rewrite from scratch).
  **Verify:** the file exists at the new path and is byte-for-byte identical to the legacy source at this point (`diff` returns no output).

- [x] **3.2 — Write adaptation tests first.** In `backend/tests/unit/test_ocr_service.py`, write tests against the **current spec** (`PRD.md` §14, §28.2): PDF→image conversion caps at exactly 3 pages; the Gemini Flash JSON schema matches `PRD.md` §14 field-for-field; malformed JSON triggers exactly 2 retries with the correction prompt before failing; fewer than 20 extracted words short-circuits to `FAILED_OCR_QUALITY` without calling Gemini at all (mock Gemini and assert it was never called in this case). Run this against the freshly-copied file and note every failure — these are the drift points mentioned in `PRD.md` §6.3.
  **Run:** `pytest backend/tests/unit/test_ocr_service.py -v` → record which tests fail.

- [x] **3.3 — Strip Lambda-specific code and adapt to failing tests.** Remove any Mangum/Lambda-handler wrapping, any Lambda-`/tmp`-specific temp-file assumptions (replace with a portable temp-directory context manager cleaned up at the end of every call, not "end of invocation"), and fix each failing test from 3.2 one at a time. Cap yourself at two fix attempts per failing test before treating it as a Stop Condition per `AGENTS.md` — do not loop indefinitely on one stubborn test.
  **Run:** `pytest backend/tests/unit/test_ocr_service.py -v` → confirm **all pass**.

- [x] **3.4 — Wire into `BackgroundTasks`.** Write an integration test asserting that calling the OCR pipeline via a `BackgroundTask` updates the `carbon-bills` DynamoDB record's `status` through `PROCESSING` → `COMPLETED`/`FAILED*` (per `DESIGN.md` §4.1), using `moto` for DynamoDB and a mocked Gemini/PaddleOCR.
  **Run:** `pytest backend/tests/integration/ -k ocr -v` → confirm pass.

- [x] **PHASE 3 GATE.** Run `pytest backend/tests/unit/test_ocr_service.py backend/tests/integration/ -k ocr -v --cov=app.services.ocr_service --cov-report=term-missing`. Confirm all green with no unexplained coverage gaps (any uncovered line must correspond to a documented, deliberately-untested branch — e.g. a genuine network-timeout path already covered by a mocked-failure test elsewhere). Commit with message `feat: OCR service adapted from v1 legacy (Phase 3)`. Do not start Phase 4 until this is green.

---

## Phase 4 — RAG Service (Adapted From Legacy v1)

- [x] **4.1 — Copy the legacy RAG implementation.** Copy `rag_service.py` (and its prompt templates) from `legacy/v1-ai-powered-esg-carbon-compliance-platform/` into `backend/app/services/rag_service.py`, unmodified, as the starting point (`PRD.md` §6.3).
  **Verify:** file exists, identical to legacy source at this point.

- [x] **4.1.1 — Create RAG Ingestion Pipeline.** Set up `backend/scripts/ingest_knowledge.py` to parse documents from `backend/data/ghg_protocol_docs` and upload their embeddings to Qdrant Cloud.
  **Verify:** `python backend/scripts/ingest_knowledge.py` runs successfully and populates the `ghg_compliance_matrix` collection.

- [x] **4.2 — Write adaptation tests first.** In `backend/tests/unit/test_rag_service.py`, write tests against `PRD.md` §15/§28.6: a mocked Qdrant top score ≥ 0.70 returns a synthesized answer + non-empty `sources`; a mocked top score < 0.70 returns the exact fallback text and empty `sources` without calling Gemini; the returned `confidence_score` exactly equals the top similarity score used for the threshold check (assert this with the identical float, not just "close enough"); a Qdrant timeout raises the correct `500`-mapped exception; 3 simulated Gemini rate-limit errors trigger exponential backoff then a `429`-mapped exception.
  **Run:** `pytest backend/tests/unit/test_rag_service.py -v` → record failures against the copied legacy code.

- [x] **4.3 — Adapt to pass.** Fix the copied logic (remove any Lambda-specific cold-start-avoidance hacks that are no longer needed now that the process stays warm per `PRD.md` §6.2, and correct the `confidence_score` computation to match §28.6 exactly if it currently diverges). Same two-fix-attempt cap as 3.3 applies per test.
  **Run:** `pytest backend/tests/unit/test_rag_service.py -v` → confirm **all pass**.

- [x] **4.4 — Golden RAG evaluation set.** Populate `backend/tests/golden/rag_eval_set.json` with the 50 compliance Q/A pairs required by `PRD.md` §19, and write `backend/tests/integration/test_rag_eval.py` asserting ≥85% judged-correct against a mocked-but-representative retrieval layer (exact judging method: string/keyword match against an expected-answer-contains list per question — define this explicitly in the test file, not left to runtime judgment).
  **Run:** `pytest backend/tests/integration/test_rag_eval.py -v` → confirm pass at ≥85%.

- [x] **PHASE 4 GATE.** Run `pytest backend/tests/unit/test_rag_service.py backend/tests/integration/test_rag_eval.py -v`. Confirm all green and the RAG eval score is printed and ≥85%. Commit with message `feat: RAG service adapted from v1 legacy (Phase 4)`. Do not start Phase 5 until this is green.

---

## Phase 5 — API Routers

- [x] **5.1 — `POST /auth/login`.** Write `backend/tests/integration/test_auth_api.py` per `DESIGN.md` §3.1 (200 success, 401 bad password, 400 malformed email — `PRD.md` §29 US-1). Implement `app/api/v1/auth.py`.
  **Run:** `pytest backend/tests/integration/test_auth_api.py -v` → confirm pass.

- [x] **5.2 — `POST /bills/upload` + `GET /bills/{bill_id}`.** Write `backend/tests/integration/test_bills_api.py` per `DESIGN.md` §3.2–3.3 and `PRD.md` §29 US-2 (202 on valid upload, 400 on oversize/unsupported type with no S3 write, terminal status always reachable, 409 on concurrent reprocess per §28.7). Implement `app/api/v1/bills.py`.
  **Run:** `pytest backend/tests/integration/test_bills_api.py -v` → confirm pass.

- [x] **5.3 — `GET /bills` (paginated list).** Add tests to the same file for `DESIGN.md` §3.4 — default page size 20, `UploadDateIndex`-backed descending sort, `next_cursor` behavior. Implement the endpoint.
  **Run:** `pytest backend/tests/integration/test_bills_api.py -v` → confirm full file green.

- [x] **5.4 — `GET /emissions/summary`.** Write `backend/tests/integration/test_emissions_api.py` per `DESIGN.md` §3.5 and `PRD.md` §29 US-3 (total exactly equals the sum of `COMPLETED` bills; scope percentages sum to 100% ± 0.1%; empty-state for zero bills). Implement `app/api/v1/emissions.py`.
  **Run:** `pytest backend/tests/integration/test_emissions_api.py -v` → confirm pass.

- [x] **5.5 — `POST /chat/query`.** Write `backend/tests/integration/test_chat_api.py` per `DESIGN.md` §3.6 and `PRD.md` §29 US-4. Implement `app/api/v1/chat.py`.
  **Run:** `pytest backend/tests/integration/test_chat_api.py -v` → confirm pass.

- [x] **PHASE 5 GATE.** Run `pytest backend/tests/integration/ -v` (every integration test written so far). Confirm all green. Also start the app locally (`docker compose up -d backend dynamodb-local`) and hit each of the 5 endpoints once with `curl`/`httpx` to confirm they respond as documented in `DESIGN.md` §3 — an automated smoke script (`backend/tests/smoke/smoke_test.sh`) should exist and be run here, not a one-off manual check. Commit with message `feat: core API routers (Phase 5)`. Do not start Phase 6 until this is green.

---

## Phase 6 — Report Service (New)

- [x] **6.1 — `app/services/report_service.py` — hotspot ranking (deterministic).** Write unit tests asserting the top 2–3 emission contributors are correctly ranked from a fixed set of `carbon-emissions` fixture records. Implement the ranking function — pure Python, no LLM involved (mirrors the calc engine's determinism rule).
  **Run:** `pytest backend/tests/unit/test_report_service.py -v` → confirm pass.

- [x] **6.2 — Numbers-only prompt construction + Gemini guardrail.** Write a test asserting the constructed prompt sent to Gemini contains only numbers present in the input data structure, and a second test asserting a post-generation check rejects (and retries once, then fails loudly rather than silently passing through) any generated report text containing a numeric CO₂e-looking value not present in the input (`PRD.md` §16.11, §29 US-5). Implement both the prompt builder and the guardrail check.
  **Run:** `pytest backend/tests/unit/test_report_service.py -v` → confirm full file green.

- [x] **6.3 — PDF assembly.** Write a test asserting the assembled PDF (via WeasyPrint) contains all 10 section headers from `PRD.md` §16.1–§16.10 in order (string-search the extracted PDF text). Implement PDF rendering.
  **Run:** `pytest backend/tests/unit/test_report_service.py -v` → confirm pass.

- [x] **6.4 — `carbon-reports` table wiring + `POST /reports/generate` + `GET /reports/{report_id}`.** Write `backend/tests/integration/test_reports_api.py` per `DESIGN.md` §3.7–3.8 and `PRD.md` §29 US-5 (202 on valid range, 400 on invalid/oversized range, 409 on concurrent identical request, all 10 sections present, zero fabricated numbers assertion running across every test-generated report). Implement `app/api/v1/reports.py`.
  **Run:** `pytest backend/tests/integration/test_reports_api.py -v` → confirm pass.

- [x] **PHASE 6 GATE.** Run `pytest backend/tests/unit/test_report_service.py backend/tests/integration/test_reports_api.py -v`. Confirm all green, including the zero-fabricated-numbers assertion running against at least 3 distinct generated test reports (not just one happy-path fixture). Commit with message `feat: report generation service (Phase 6)`. Do not start Phase 7 until this is green.

---

## Phase 7 — Backend Integration Gate

- [x] **7.1 — Full backend suite + coverage gate.** Run the complete backend command from `TECH_STACK.md` §9.
  **Run:** `cd backend && pytest --cov=app --cov-report=term-missing --cov-fail-under=80` → confirm pass at ≥80% overall, with `calc_engine.py` still individually verified at 100% (re-run 2.2's command to double check).

- [x] **7.2 — Lint + security gate.** Run `black --check`, `flake8`, `mypy`, and `bandit` exactly as specified in `TECH_STACK.md` §8-9.
  **Run:** all four commands → confirm zero errors/warnings that block CI.

- [x] **PHASE 7 GATE.** This phase's own two tasks already are the gate — if both 7.1 and 7.2 are green, the entire backend is done and verified. Tag the repo state (`git tag backend-complete`) before moving to frontend work. Do not start Phase 8 until 7.1 and 7.2 are both green.

---

## Phase 8 — Frontend Scaffolding

- [x] **8.1 — Next.js app init.** Create `frontend/` with Next.js 14 App Router, TypeScript, Tailwind CSS, ESLint, per `TECH_STACK.md` §5 and `DESIGN.md` §1. Configure `pnpm-workspace.yaml` to include it.
  **Verify:** `pnpm --filter frontend dev` boots the default page with no errors.

- [x] **8.2 — Monochrome design tokens.** Implement the full color token set and `Geist`/`Geist Mono` font loading exactly per `PRD.md` §10.1–10.2 in `tailwind.config.ts` and `app/globals.css`. Write a component test asserting no Tailwind color class other than the defined grayscale tokens is used in any committed component (a simple grep-based test script is acceptable here, run as part of `pnpm --filter frontend test`).
  **Run:** `pnpm --filter frontend test` → confirm the token-usage check passes.

- [x] **8.3 — shadcn/ui setup.** Initialize shadcn/ui, generate the primitives needed (Button, Input, Card, Table, Dialog, Toast, Skeleton) restyled to the monochrome tokens from 8.2 (no default shadcn color theme left in place).
  **Verify:** a sample page renders each primitive with the correct monochrome styling (visual check via `pnpm --filter frontend dev`, plus a snapshot test).

- [x] **8.4 — `lib/api-client.ts`.** Write a unit test asserting: requests attach the JWT cookie/header correctly; a `401` response triggers session clear + redirect to `/login` (per `PRD.md` §18/§28.1); a `500` response surfaces a generic toast trigger. Implement the fetch wrapper (no `axios` — see `TECH_STACK.md` §12).
  **Run:** `pnpm --filter frontend test` → confirm the new test file passes.

- [x] **PHASE 8 GATE.** Run `pnpm --filter frontend lint` and `pnpm --filter frontend test`. Confirm both clean/green, and confirm `pnpm --filter frontend build` succeeds (production build, not just dev server). Commit with message `feat: frontend scaffolding + design system (Phase 8)`. Do not start Phase 9 until this is green.

---

## Phase 9 — Frontend Pages (One Per User Story)

- [x] **9.1 — Auth page (`/login`).** Write a component test (React Hook Form + Zod validation, error display) and a Playwright E2E test for the full login flow. Implement the page.
  **Run:** `pnpm --filter frontend test` then `pnpm --filter frontend test:e2e -- --grep login` → confirm both pass.

- [x] **9.2 — Upload page (`/upload`).** Write tests for: drag-and-drop states, the 15MB/type client-side validation (matching `PRD.md` §28.2 exactly), progress display, and redirect to bill details on `202`. Implement the page and `components/upload-dropzone.tsx`.
  **Run:** `pnpm --filter frontend test` → confirm pass.

- [x] **9.3 — Bill Details page (`/bills/[id]`).** Write tests for: polling behavior via TanStack Query until a terminal status, split-view rendering (document viewer + editable extracted-data form), "Confirm & Calculate"/"Recalculate" actions. Implement the page.
  **Run:** `pnpm --filter frontend test` → confirm pass.

- [x] **9.4 — Dashboard page (`/dashboard`).** Write tests for: stat cards rendering from `/emissions/summary`, the grayscale Scope 1/2/3 chart (`components/scope-chart.tsx`, using the pattern-fill rule from `PRD.md` §10.1 for accessibility), the empty state for zero bills (`PRD.md` §29 US-3). Implement the page.
  **Run:** `pnpm --filter frontend test` → confirm pass.

- [x] **9.5 — Chat page (`/chat`).** Write tests for: message list rendering, markdown rendering of AI responses, source citation display, the "AI is thinking..." state, and correct handling of the low-confidence fallback response. Implement the page and `components/chat-window.tsx`.
  **Run:** `pnpm --filter frontend test` → confirm pass.

- [x] **9.6 — Reports page (`/reports`).** Write tests for: date-range picker validation (matching `PRD.md` §28.5's `period_start < period_end`, ≤366-day rule client-side too), generation trigger, polling for `download_url`, and download action. Implement the page.
  **Run:** `pnpm --filter frontend test` → confirm pass.

- [x] **9.7 — Settings page (`/settings`).** Write tests for: currency-code selection (set-once behavior per `PRD.md` §28.4 — field becomes read-only after first save), company profile display. Implement the page.
  **Run:** `pnpm --filter frontend test` → confirm pass.

- [x] **PHASE 9 GATE.** Run `pnpm --filter frontend test` (full unit/component suite) and `pnpm --filter frontend test:e2e` (every E2E spec written so far, one per page). Confirm all green. Commit with message `feat: all frontend pages (Phase 9)`. Do not start Phase 10 until this is green.

---

## Phase 10 — End-to-End Coverage

- [x] **10.1 — Full E2E happy path.** Write one Playwright test walking the entire flow: login → upload a fixture bill → wait for `COMPLETED` → dashboard reflects the new emissions → ask a chat question → generate a report → download it. This must run against `docker compose up` (real backend + frontend, mocked external APIs at the network boundary only).
  **Run:** `pnpm --filter frontend test:e2e` → confirm this new test passes alongside all prior E2E tests.

- [x] **10.2 — Full local CI gate.** Run `./scripts/check.sh` from the repo root.
  **Run:** confirm output ends with `ALL GREEN` and no step above it failed.

- [x] **PHASE 10 GATE.** This phase's two tasks already are the gate. If 10.1 and 10.2 are both green, the entire application is functionally complete and self-verified end-to-end. Tag the repo (`git tag app-complete`) before moving to deployment.

---

## Phase 11 — Deployment

- [ ] **11.1 - `backend/Dockerfile`.** Multi-stage build (install deps -> copy app -> run via `gunicorn -k uvicorn.workers.UvicornWorker`). Add a `GET /health` endpoint returning `200 {"status": "ok"}` if not already present. Write a smoke test: build the image and `docker run` it, then `curl` the health-check endpoint.
  **Run:** `docker build -t carbon-auditor-backend ./backend && docker run -d -p 8000:8000 carbon-auditor-backend && curl -f http://localhost:8000/health` -> confirm `200`.

- [ ] **11.2 - `render.yaml` Blueprint.** Create a `render.yaml` Blueprint to automatically deploy the backend Docker container on Render's free tier. Define all required environment variables, including `sync: false` for secrets.
  **Run:** Review `render.yaml` and confirm the configuration targets the `backend/Dockerfile`.

- [ ] **11.3 - AWS IAM & S3/DynamoDB Provisioning.** Since the backend is moving to the cloud, the user must provision a free-tier AWS DynamoDB table and S3 bucket, and generate IAM credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) to enter into Render.
  **Run:** Wait for user to provide the AWS credentials and load them into Render dashboard.

- [ ] **11.4 - Vercel connection.** Connect the `frontend/` directory as the Vercel project root; set `NEXT_PUBLIC_API_BASE_URL` to the live Render backend URL (e.g., `https://carbon-backend.onrender.com`).
  **Run:** confirm the Vercel preview/production deployment loads the login page and can successfully call the live backend.

- [ ] **11.5 - CI workflows finalized.** Update `.github/workflows/backend-ci.yml` and `frontend-ci.yml` (from Phase 0.6) to run the exact final commands from `TECH_STACK.md`, and confirm both pass on a fresh push to the default branch.
  **Run:** push to `main` (or open a PR) and confirm both GitHub Actions workflows report green.

- [ ] **PHASE 11 GATE (Project Done Gate).** Confirm every one of the following in one pass: `./scripts/check.sh` reports `ALL GREEN`; the Phase 10 E2E happy path still passes against the deployed (not just local) backend URL; the live Vercel frontend loads and functions against the live Render backend; both GitHub Actions workflows are green on `main`. Only once all four are true is this roadmap complete — see "Done Criteria" below.

---

## Done Criteria

This roadmap is complete only when every checkbox above is checked, every Phase Gate is green, `./scripts/check.sh` reports `ALL GREEN`, the E2E happy path (10.1) passes both locally and against the deployed backend, and the live Vercel + Render deployment is reachable and functional end-to-end.
