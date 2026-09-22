import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routes import health, ocr
from app.services.ocr_service import OCRService
from app.utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI.
    Initializes the PaddleOCR singleton on startup.
    """
    logger.info("Initializing application lifespan...")
    
    # Initialize OCR Service
    try:
        logger.info("Loading PaddleOCR model (this may take a moment)...")
        OCRService.get_instance()
        logger.info("PaddleOCR model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load PaddleOCR model: {e}")
        # We don't raise here so the health endpoint can still run and indicate the error
    
    yield
    
    logger.info("Application shutting down...")

# Create FastAPI application
app = FastAPI(
    title="OCR Microservice",
    description="A production-ready OCR Microservice using FastAPI and PaddleOCR.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(ocr.router)
