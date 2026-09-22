import re
from typing import List, Dict, Any
from app.core.config import settings
from app.core.llm_client import OpenRouterClient

llm = OpenRouterClient()


class ReportGuardrailError(Exception):
    pass


def get_hotspots(
    emissions: List[Dict[str, Any]], top_n: int = 3
) -> List[Dict[str, Any]]:
    """
    Ranks a list of emission records by value_kg (descending) and returns the top_n items.
    Pure python, deterministic ranking.
    """
    sorted_emissions = sorted(
        emissions, key=lambda x: x.get("value_kg", 0.0), reverse=True
    )
    return sorted_emissions[:top_n]


def build_report_prompt(
    company_name: str, start_date: str, end_date: str, emissions: List[Dict[str, Any]]
) -> str:
    """
    Builds the prompt using strictly only the numbers provided in the input.
    """
    prompt = f"Generate a carbon emissions report for {company_name} from {start_date} to {end_date}.\n"
    prompt += "Use EXACTLY the following data. Do NOT fabricate or estimate any other numbers.\n"
    prompt += "Do NOT perform any calculations. Use only these numbers:\n\n"
    
    total = 0.0
    for e in emissions:
        val = float(e.get('value_kg', 0))
        total += val
        prompt += f"- {e.get('source')}: {val} kg CO2e\n"

    prompt += f"- Total Emissions: {total} kg CO2e\n"

    prompt += "\nFormat the report into exactly these 4 sections to be concise:\n"
    prompt += "1. Executive Summary\n"
    prompt += "2. Scope Breakdown\n"
    prompt += "3. Hotspot Identification\n"
    prompt += "4. Recommendations & Conclusion\n"
    return prompt


def validate_report_numbers(report_text: str, emissions: List[Dict[str, Any]]) -> bool:
    """
    Validates that any numeric CO2e-looking value in the report was actually in the input.
    """
    # Get allowed numbers from emissions
    allowed = set()
    total = 0.0
    for e in emissions:
        val = float(e.get('value_kg', 0))
        allowed.add(str(val))
        allowed.add(str(int(val)) if val.is_integer() else str(val))
        total += val
        
    allowed.add(str(total))
    allowed.add(str(int(total)) if total.is_integer() else str(total))

    # Also allow integers 1-10 for section numbers, and year/month/day parts
    # A real robust check would look closely at "X kg CO2e" patterns.
    # We will look for numbers that appear right before "kg CO2e" or similar.
    # PRD says "any generated report text containing a numeric CO2e-looking value not present in the input"
    co2e_numbers = set(
        re.findall(
            r"\b(\d+(?:\.\d+)?)\s*(?:kg CO2e|CO2e|kg)\b", report_text, re.IGNORECASE
        )
    )

    unexpected = co2e_numbers - allowed
    if unexpected:
        raise ReportGuardrailError(f"Fabricated numbers detected: {unexpected}")

    return True


async def call_gemini(prompt: str) -> str:
    response = await llm.generate_content(prompt)
    return response


async def generate_report_content(
    company_name: str, start_date: str, end_date: str, emissions: List[Dict[str, Any]]
) -> str:
    prompt = build_report_prompt(company_name, start_date, end_date, emissions)

    max_retries = 2
    for attempt in range(max_retries):
        report_text = await call_gemini(prompt)
        try:
            validate_report_numbers(report_text, emissions)
            return report_text
        except ReportGuardrailError as e:
            if attempt == max_retries - 1:
                raise e

    raise ReportGuardrailError("Max retries exceeded")


def generate_pdf(report_text: str, company_name: str) -> bytes:
    from markdown_pdf import MarkdownPdf, Section
    import io

    pdf = MarkdownPdf(toc_level=2)
    pdf.meta["title"] = f"Carbon Emissions Report: {company_name}"
    
    # Add a title at the top of the report text
    full_text = f"# Carbon Emissions Report: {company_name}\n\n{report_text}"
    
    pdf.add_section(Section(full_text))
    
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp_path = tmp.name
        
    try:
        pdf.save(tmp_path)
        with open(tmp_path, "rb") as f:
            pdf_bytes = f.read()
    finally:
        os.remove(tmp_path)
        
    return pdf_bytes
