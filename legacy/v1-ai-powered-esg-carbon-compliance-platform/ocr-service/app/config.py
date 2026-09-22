import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application settings, loaded from environment variables or .env file.
    """
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", 20971520))  # Default 20MB
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Allowed MIME types for uploaded files
    ALLOWED_MIME_TYPES: set[str] = {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/webp",
        "image/tiff",
    }
    
    # Allowed extensions for uploaded files
    ALLOWED_EXTENSIONS: set[str] = {
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".tiff",
        ".tif"
    }

settings = Settings()
