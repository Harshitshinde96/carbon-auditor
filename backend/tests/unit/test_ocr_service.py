import pytest
from unittest.mock import patch, MagicMock
from app.services.ocr_service import process_bill_ocr
from app.core.exceptions import OCRProcessingError


@pytest.fixture
def mock_markitdown():
    with patch("app.services.ocr_service.MarkItDown") as MockMID:
        mock_instance = MockMID.return_value
        yield mock_instance


@pytest.fixture
def mock_gemini():
    with patch("app.services.ocr_service.genai") as mock_genai:
        yield mock_genai


def test_gemini_json_schema(mock_markitdown, mock_gemini):
    mock_result = MagicMock()
    mock_result.text_content = "word " * 25
    mock_markitdown.convert.return_value = mock_result

    mock_model = mock_gemini.GenerativeModel.return_value
    mock_model.generate_content.return_value.text = '{"utility_type": "Electricity", "consumption": 100, "unit": "kWh", "cost": 50.0, "period_start": "2024-01-01", "period_end": "2024-01-31"}'

    result = process_bill_ocr("dummy.xlsx", "bill_123")
    assert result["utility_type"] == "Electricity"
    assert "cost" in result
    assert "period_start" in result

    mock_markitdown.convert.assert_called_with("dummy.xlsx")


def test_malformed_json_retries_twice(mock_markitdown, mock_gemini):
    mock_result = MagicMock()
    mock_result.text_content = "word " * 25
    mock_markitdown.convert.return_value = mock_result

    mock_model = mock_gemini.GenerativeModel.return_value
    # Fail 3 times total (initial + 2 retries)
    mock_model.generate_content.return_value.text = "invalid json"

    with pytest.raises(OCRProcessingError):
        process_bill_ocr("dummy.png", "bill_123")

    assert mock_model.generate_content.call_count == 3


def test_fewer_than_20_words_short_circuit(mock_markitdown, mock_gemini):
    mock_result = MagicMock()
    mock_result.text_content = "word " * 10
    mock_markitdown.convert.return_value = mock_result
    mock_model = mock_gemini.GenerativeModel.return_value

    with pytest.raises(OCRProcessingError) as exc:
        process_bill_ocr("dummy.docx", "bill_123")

    assert "FAILED_OCR_QUALITY" in str(exc.value)
    mock_model.generate_content.assert_not_called()


def test_markitdown_failure(mock_markitdown):
    mock_markitdown.convert.side_effect = Exception("File corrupted")

    with pytest.raises(OCRProcessingError) as exc:
        process_bill_ocr("corrupt.pdf", "bill_123")

    assert "MarkItDown conversion failed" in str(exc.value)
