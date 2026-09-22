import os
import shutil
import uuid
from pathlib import Path
from fastapi import UploadFile
from typing import Tuple

TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

async def save_upload_file_tmp(upload_file: UploadFile) -> Path:
    """
    Saves an uploaded file to a temporary directory.
    Returns the path to the saved file.
    """
    try:
        suffix = Path(upload_file.filename).suffix
        temp_file = TEMP_DIR / f"{uuid.uuid4()}{suffix}"
        
        with temp_file.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
            
        return temp_file
    finally:
        upload_file.file.close()

def remove_temp_file(file_path: Path) -> None:
    """
    Deletes a temporary file if it exists.
    """
    try:
        if file_path.exists():
            os.remove(file_path)
    except Exception as e:
        # We don't want to fail the request if cleanup fails, but we should log it
        from app.utils.logger import logger
        logger.error(f"Failed to delete temporary file {file_path}: {e}")

def remove_temp_dir(dir_path: Path) -> None:
    """
    Deletes a temporary directory and its contents if it exists.
    """
    try:
        if dir_path.exists() and dir_path.is_dir():
            shutil.rmtree(dir_path)
    except Exception as e:
        from app.utils.logger import logger
        logger.error(f"Failed to delete temporary directory {dir_path}: {e}")
