#!/usr/bin/env bash
# =============================================================================
# Carbon Auditor — Local CI Gate
# Run this before marking any TASKS.md checkbox complete.
# Usage: ./scripts/check.sh
# =============================================================================
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          Carbon Auditor — Full Local CI Check                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ── Backend lint ──────────────────────────────────────────────────────────────
echo "▶  [1/5] Backend lint (black, flake8, mypy) ..."
cd "$REPO_ROOT/backend"
source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null || true

black --check app tests
flake8 app tests
mypy app
echo "   ✓ Backend lint PASSED"

# ── Backend tests ─────────────────────────────────────────────────────────────
echo ""
echo "▶  [2/5] Backend tests (pytest --cov ≥80%) ..."
pytest --cov=app --cov-report=term-missing --cov-fail-under=80
echo "   ✓ Backend tests PASSED"

cd "$REPO_ROOT"

# ── Frontend lint ─────────────────────────────────────────────────────────────
echo ""
echo "▶  [3/5] Frontend lint (next lint) ..."
pnpm --filter frontend lint
echo "   ✓ Frontend lint PASSED"

# ── Frontend unit/component tests ─────────────────────────────────────────────
echo ""
echo "▶  [4/5] Frontend unit tests (jest) ..."
pnpm --filter frontend test
echo "   ✓ Frontend unit tests PASSED"

# ── Frontend build ────────────────────────────────────────────────────────────
echo ""
echo "▶  [5/5] Frontend production build ..."
NEXT_TELEMETRY_DISABLED=1 pnpm --filter frontend build
echo "   ✓ Frontend build PASSED"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                     ALL GREEN ✓                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
