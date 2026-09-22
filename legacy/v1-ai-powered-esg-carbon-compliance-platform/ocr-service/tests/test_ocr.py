import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from PIL import Image

client = TestClient(app)

def create_dummy_image():
    """Creates a simple dummy image for testing upload without needing a real file."""
    image = Image.new('RGB', (100, 100), color = 'white')
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def test_ocr_no_file():
    response = client.post("/ocr")
    assert response.status_code == 422 # Unprocessable Entity (FastAPI validation)

def test_ocr_unsupported_format():
    files = {'file': ('test.txt', b'dummy content', 'text/plain')}
    response = client.post("/ocr", files=files)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Unsupported file format" in data["error"]

def test_ocr_large_file():
    # Simulate a file larger than MAX_FILE_SIZE (20MB)
    # Actually, generating a 21MB in-memory file might be slow, so let's mock the config
    from app.config import settings
    original_max_size = settings.MAX_FILE_SIZE
    settings.MAX_FILE_SIZE = 10  # 10 bytes limit for test
    
    files = {'file': ('test.png', b'this is more than 10 bytes', 'image/png')}
    response = client.post("/ocr", files=files)
    
    settings.MAX_FILE_SIZE = original_max_size # restore
    
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "File too large" in data["error"]

def test_ocr_valid_image():
    # Test with a valid dummy image
    # Note: If PaddleOCR is not installed/loaded, this might fail during OCR processing,
    # but the routing and file handling should work. 
    # For CI/CD, you might want to mock the OCRService.extract_text method.
    img_bytes = create_dummy_image()
    files = {'file': ('dummy.png', img_bytes, 'image/png')}
    
    # We use a mocked OCR service so we don't need paddleocr models downloaded just to run basic routing tests
    from app.services.ocr_service import OCRService
    
    # Mocking the OCR extract
    original_extract = OCRService.extract_text
    
    def mock_extract(self, path):
        return "Mocked extracted text", 0.99
        
    OCRService.extract_text = mock_extract
    
    try:
        response = client.post("/ocr", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["filename"] == "dummy.png"
        assert data["pages"] == 1
        assert "Mocked extracted text" in data["text"]
        assert data["metadata"]["engine"] == "PaddleOCR"
    finally:
        # Restore mock
        OCRService.extract_text = original_extract
