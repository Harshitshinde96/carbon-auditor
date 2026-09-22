"""Carbon Auditor — FastAPI application entry point."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import CarbonBaseException

app = FastAPI(
    title="Carbon Auditor API",
    version="0.1.0",
    description="AI-powered carbon footprint tracking and compliance platform.",
)

@app.exception_handler(CarbonBaseException)
async def carbon_exception_handler(request: Request, exc: CarbonBaseException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "code": exc.status_code,
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "code": 422,
            "message": "Validation error",
            "details": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "code": 500,
            "message": "Internal server error",
            "details": []
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
