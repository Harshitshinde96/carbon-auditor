# Carbon Auditor - Local CI Gate (PowerShell version for Windows)
# Run from repo root: .\scripts\check.ps1

$ErrorActionPreference = "Stop"
$REPO_ROOT = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "          Carbon Auditor - Full Local CI Check                " -ForegroundColor Cyan
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host ""

# -- Backend lint --------------------------------------------------------------
Write-Host "-> [1/5] Backend lint (black, flake8, mypy) ..." -ForegroundColor Yellow

Push-Location "$REPO_ROOT\backend"
try {
    & ".\.venv\Scripts\activate.ps1"
    black --check app tests
    if ($LASTEXITCODE -ne 0) { throw "black failed" }
    flake8 app tests
    if ($LASTEXITCODE -ne 0) { throw "flake8 failed" }
    mypy app
    if ($LASTEXITCODE -ne 0) { throw "mypy failed" }
    Write-Host "   OK Backend lint PASSED" -ForegroundColor Green
} finally {
    Pop-Location
}

# -- Backend tests -------------------------------------------------------------
Write-Host ""
Write-Host "-> [2/5] Backend tests (pytest --cov >=80%) ..." -ForegroundColor Yellow

Push-Location "$REPO_ROOT\backend"
try {
    & ".\.venv\Scripts\activate.ps1"
    pytest --cov=app --cov-report=term-missing --cov-fail-under=80
    if ($LASTEXITCODE -ne 0) { throw "pytest failed" }
    Write-Host "   OK Backend tests PASSED" -ForegroundColor Green
} finally {
    Pop-Location
}

# -- Frontend lint -------------------------------------------------------------
Write-Host ""
Write-Host "-> [3/5] Frontend lint (next lint) ..." -ForegroundColor Yellow

Push-Location "$REPO_ROOT\frontend"
try {
    pnpm run lint
    if ($LASTEXITCODE -ne 0) { throw "Frontend lint failed" }
    Write-Host "   OK Frontend lint PASSED" -ForegroundColor Green
} finally {
    Pop-Location
}

# -- Frontend unit/component tests ---------------------------------------------
Write-Host ""
Write-Host "-> [4/5] Frontend unit tests (jest) ..." -ForegroundColor Yellow

Push-Location "$REPO_ROOT\frontend"
try {
    pnpm run test
    if ($LASTEXITCODE -ne 0) { throw "Frontend tests failed" }
    Write-Host "   OK Frontend unit tests PASSED" -ForegroundColor Green
} finally {
    Pop-Location
}

# -- Frontend build ------------------------------------------------------------
Write-Host ""
Write-Host "-> [5/5] Frontend production build ..." -ForegroundColor Yellow

Push-Location "$REPO_ROOT\frontend"
try {
    $env:NEXT_TELEMETRY_DISABLED = "1"
    pnpm run build
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed" }
    Write-Host "   OK Frontend build PASSED" -ForegroundColor Green
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "==============================================================" -ForegroundColor Green
Write-Host "                     ALL GREEN                                " -ForegroundColor Green
Write-Host "==============================================================" -ForegroundColor Green
Write-Host ""
