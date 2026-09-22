import pytest
import re
from unittest.mock import AsyncMock, patch
from app.services.report_service import (
    get_hotspots,
    build_report_prompt,
    validate_report_numbers,
    ReportGuardrailError,
    generate_report_content,
)


def test_get_hotspots():
    emissions = [
        {"emission_id": "1", "source": "electricity", "value_kg": 5000.0},
        {"emission_id": "2", "source": "flights", "value_kg": 20000.0},
        {"emission_id": "3", "source": "heating", "value_kg": 1500.0},
        {"emission_id": "4", "source": "commute", "value_kg": 3000.0},
        {"emission_id": "5", "source": "freight", "value_kg": 8000.0},
    ]

    hotspots = get_hotspots(emissions, top_n=3)
    assert len(hotspots) == 3
    assert hotspots[0]["source"] == "flights"


def test_build_report_prompt_contains_only_input_numbers():
    emissions = [
        {"emission_id": "1", "source": "electricity", "value_kg": 500.5},
        {"emission_id": "2", "source": "flights", "value_kg": 1000.0},
    ]
    prompt = build_report_prompt("Company X", "2023-01-01", "2023-12-31", emissions)

    # Extract all numbers from prompt
    numbers_in_prompt = set(re.findall(r"\b\d+(?:\.\d+)?\b", prompt))

    # Allowed numbers
    allowed = {"500.5", "1000.0", "1", "2", "2023", "01", "12", "31"}

    # Remove any number that is part of the section numbering in PRD (like 1 to 10)
    for i in range(1, 11):
        allowed.add(str(i))

    # Check if there are any unexpected numbers
    unexpected = numbers_in_prompt - allowed
    assert not unexpected, f"Prompt contains unexpected numbers: {unexpected}"


def test_validate_report_numbers():
    emissions = [
        {"emission_id": "1", "source": "electricity", "value_kg": 500.5},
        {"emission_id": "2", "source": "flights", "value_kg": 1000.0},
    ]

    # Valid report
    valid_report = (
        "Total is 1000.0 kg CO2e for flights and 500.5 kg CO2e for electricity."
    )
    assert validate_report_numbers(valid_report, emissions) is True

    # Invalid report hallucinating a number (999.9)
    invalid_report = "Total is 999.9 kg CO2e for flights."
    with pytest.raises(ReportGuardrailError):
        validate_report_numbers(invalid_report, emissions)


@pytest.mark.asyncio
async def test_generate_report_retries_on_hallucination():
    emissions = [{"emission_id": "1", "source": "electricity", "value_kg": 500.5}]

    # Mock gemini to first return a hallucinated number, then a valid one
    mock_generate = AsyncMock(
        side_effect=["Hallucinated: 999.9 kg CO2e", "Valid: 500.5 kg CO2e"]
    )

    with patch("app.services.report_service.call_gemini", mock_generate):
        result = await generate_report_content(
            "Company X", "2023-01-01", "2023-12-31", emissions
        )
        assert "500.5" in result
        assert mock_generate.call_count == 2


@pytest.mark.asyncio
async def test_generate_report_fails_loudly():
    emissions = [{"emission_id": "1", "source": "electricity", "value_kg": 500.5}]

    # Mock gemini to return hallucinated numbers twice
    mock_generate = AsyncMock(
        side_effect=["Hallucinated: 999.9 kg CO2e", "Hallucinated again: 888.8 kg CO2e"]
    )

    with patch("app.services.report_service.call_gemini", mock_generate):
        with pytest.raises(ReportGuardrailError):
            await generate_report_content(
                "Company X", "2023-01-01", "2023-12-31", emissions
            )


def test_generate_pdf():
    from app.services.report_service import generate_pdf
    import pypdfium2 as pdfium
    import io

    report_text = """
1. Boundary & Methodology
Content here.
2. Scope Breakdown
Content here.
3. Hotspot Identification
Content here.
4. Recommendations
Content here.
5. Data Quality Disclosure
Content here.
6. Conclusion
Content here.
7. Executive Summary
Content here.
8. Emissions by Facility
Content here.
9. Trend Analysis
Content here.
10. Appendix
Content here.
"""
    try:
        pdf_bytes = generate_pdf(report_text, "Company X")
    except OSError:
        pytest.skip("WeasyPrint missing GTK dependencies on this platform")
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0

    # Extract text to verify headers
    pdf = pdfium.PdfDocument(io.BytesIO(pdf_bytes))
    text = ""
    for page in pdf:
        text += page.get_textpage().get_text_range()

    headers = [
        "Boundary & Methodology",
        "Scope Breakdown",
        "Hotspot Identification",
        "Recommendations",
        "Data Quality Disclosure",
        "Conclusion",
        "Executive Summary",
        "Emissions by Facility",
        "Trend Analysis",
        "Appendix",
    ]

    # Check that they exist in order
    print("PDF TEXT:")
    print(text)

    last_idx = -1
    for h in headers:
        idx = text.find(h)
        assert idx != -1, f"Header '{h}' not found in PDF text"
        assert idx > last_idx, f"Header '{h}' appears out of order"
        last_idx = idx
