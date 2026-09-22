from pydantic import BaseModel, Field
from typing import Optional

class OCRMetadata(BaseModel):
    engine: str = Field(default="PaddleOCR")
    language: str = Field(default="en")
    confidence: float

class OCRResponse(BaseModel):
    success: bool
    filename: str
    pages: int
    text: str
    processingTime: float
    metadata: OCRMetadata

class HealthResponse(BaseModel):
    status: str
    ocr: str
    timestamp: str

class RootResponse(BaseModel):
    service: str
    status: str

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
