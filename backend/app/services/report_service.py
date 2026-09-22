import re
import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict
from decimal import Decimal
from app.core.llm_client import OpenRouterClient

llm = OpenRouterClient()


class ReportGuardrailError(Exception):
    pass


# ─── Emission Factor Reference (PRD §13) ───────────────────────────────────
EMISSION_FACTORS = [
    {
        "utility_type": "Electricity",
        "scope": "Scope 2",
        "category": "Purchased Electricity",
        "factor": "0.385 kg CO₂e / kWh",
        "source": "US EPA National Average",
    },
    {
        "utility_type": "Natural Gas",
        "scope": "Scope 1",
        "category": "Stationary Combustion",
        "factor": "5.3 kg CO₂e / Therm",
        "source": "GHG Protocol Default",
    },
    {
        "utility_type": "Water",
        "scope": "Scope 3",
        "category": "Purchased Goods & Services",
        "factor": "0.344 kg CO₂e / 1000 Gallons",
        "source": "GHG Protocol Default",
    },
]


# ─── Deterministic Pre-Computation (Pure Python, No LLM) ───────────────────

def precompute_report_data(
    emissions: List[Dict[str, Any]],
    bills: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Pre-computes ALL numeric data for the report from DynamoDB records.
    Every number in the final report originates from this function.
    The LLM never computes anything.
    """
    # ── Scope Breakdown ──
    scope_totals: Dict[str, float] = {"SCOPE_1": 0.0, "SCOPE_2": 0.0, "SCOPE_3": 0.0}
    utility_totals: Dict[str, float] = defaultdict(float)
    monthly_totals: Dict[str, float] = defaultdict(float)
    total_kg = 0.0

    for e in emissions:
        kg = float(e.get("co2e_kg", 0))
        scope = e.get("scope", "UNKNOWN")
        utility = e.get("utility_type", "UNKNOWN")

        total_kg += kg
        if scope in scope_totals:
            scope_totals[scope] += kg
        utility_totals[utility] += kg

        # Extract month from emission_date (format: "YYYY-MM-DD#bill_id" or "YYYY-MM-DD")
        raw_date = e.get("emission_date", "")
        date_part = raw_date.split("#")[0] if "#" in raw_date else raw_date
        if len(date_part) >= 7:
            month_key = date_part[:7]  # "YYYY-MM"
            monthly_totals[month_key] += kg

    total_tonnes = round(total_kg / 1000, 4)

    # ── Scope percentages ──
    scope_breakdown = []
    for scope_key, scope_label, category_label in [
        ("SCOPE_1", "Scope 1", "Stationary Combustion (Natural Gas)"),
        ("SCOPE_2", "Scope 2", "Purchased Electricity"),
        ("SCOPE_3", "Scope 3", "Purchased Goods & Services (Water)"),
    ]:
        val_kg = round(scope_totals[scope_key], 2)
        val_t = round(val_kg / 1000, 4)
        pct = round((val_kg / total_kg * 100), 1) if total_kg > 0 else 0.0
        scope_breakdown.append({
            "scope": scope_label,
            "category": category_label,
            "kg": val_kg,
            "tonnes": val_t,
            "pct": pct,
        })

    # ── Utility-type breakdown ──
    utility_breakdown = []
    for utype, val_kg in sorted(utility_totals.items(), key=lambda x: -x[1]):
        pct = round((val_kg / total_kg * 100), 1) if total_kg > 0 else 0.0
        utility_breakdown.append({
            "utility_type": utype,
            "kg": round(val_kg, 2),
            "tonnes": round(val_kg / 1000, 4),
            "pct": pct,
        })

    # ── Hotspot ranking ──
    hotspots = utility_breakdown[:3]  # Already sorted descending

    # ── Monthly trend (sorted chronologically) ──
    monthly_trend = []
    for month_key in sorted(monthly_totals.keys()):
        monthly_trend.append({
            "month": month_key,
            "kg": round(monthly_totals[month_key], 2),
        })

    # ── Bill-level traceability ──
    bill_register = []
    if bills:
        for b in bills:
            if b.get("status") != "COMPLETED":
                continue
            extracted = b.get("extracted_data", {})
            emis = b.get("emissions", {})
            bill_register.append({
                "bill_id": b.get("bill_id", "N/A")[:8] + "...",
                "date": extracted.get("billing_period_start", "N/A"),
                "utility_type": extracted.get("utility_type", "N/A"),
                "consumption": str(extracted.get("consumption", "N/A")),
                "unit": extracted.get("unit", "N/A"),
                "cost": str(extracted.get("cost", "N/A")),
                "co2e_kg": str(emis.get("calculated_co2e_kg", "N/A")),
                "scope": emis.get("scope", "N/A"),
            })

    return {
        "total_kg": round(total_kg, 2),
        "total_tonnes": total_tonnes,
        "scope_breakdown": scope_breakdown,
        "utility_breakdown": utility_breakdown,
        "hotspots": hotspots,
        "monthly_trend": monthly_trend,
        "bill_register": bill_register,
        "num_bills": len(bill_register),
        "num_emission_records": len(emissions),
    }


# ─── Deterministic Markdown Sections (No LLM) ──────────────────────────────

def build_deterministic_sections(
    company_name: str,
    start_date: str,
    end_date: str,
    data: Dict[str, Any],
) -> str:
    """
    Builds sections §16.3–§16.7 and §16.10 as deterministic Markdown.
    These sections contain ONLY pre-computed numbers — no LLM involvement.
    """
    sections = []

    # ── §16.3 Total Emissions Summary ──
    sections.append("## 3. Total Emissions Summary\n")
    sections.append(f"**Reporting Period:** {start_date} to {end_date}\n")
    sections.append(f"**Total Emissions:** {data['total_kg']} kg CO₂e ({data['total_tonnes']} metric tons CO₂e)\n")
    sections.append("")
    sections.append("| Scope | Category | kg CO₂e | Metric Tons CO₂e | % of Total |")
    sections.append("|-------|----------|---------|------------------|------------|")
    for s in data["scope_breakdown"]:
        sections.append(f"| {s['scope']} | {s['category']} | {s['kg']} | {s['tonnes']} | {s['pct']}% |")
    sections.append("")

    # ── §16.4 Scope 1/2/3 Breakdown ──
    sections.append("## 4. Scope 1 / Scope 2 / Scope 3 Breakdown\n")
    for s in data["scope_breakdown"]:
        bar_len = max(1, int(s["pct"] / 2))
        bar = "█" * bar_len
        sections.append(f"- **{s['scope']} — {s['category']}:** {s['kg']} kg CO₂e ({s['pct']}%) {bar}")
    sections.append("")

    # ── §16.5 Emissions by Utility Type ──
    sections.append("## 5. Emissions by Source / Utility Type\n")
    sections.append("| Utility Type | kg CO₂e | Metric Tons CO₂e | % of Total |")
    sections.append("|-------------|---------|------------------|------------|")
    for u in data["utility_breakdown"]:
        sections.append(f"| {u['utility_type']} | {u['kg']} | {u['tonnes']} | {u['pct']}% |")
    sections.append("")

    # ── §16.6 Monthly Trend ──
    sections.append("## 6. Monthly Emissions Trend\n")
    if data["monthly_trend"]:
        sections.append("| Month | kg CO₂e |")
        sections.append("|-------|---------|")
        for m in data["monthly_trend"]:
            sections.append(f"| {m['month']} | {m['kg']} |")
    else:
        sections.append("*No monthly trend data available for this period.*")
    sections.append("")

    # ── §16.7 Emission Hotspot Identification ──
    sections.append("## 7. Emission Hotspot Identification\n")
    if data["hotspots"]:
        sections.append("The following are the top emission contributors ranked by total CO₂e:\n")
        for i, h in enumerate(data["hotspots"], 1):
            sections.append(f"**#{i}: {h['utility_type']}** — {h['kg']} kg CO₂e ({h['pct']}% of total emissions)")
    else:
        sections.append("*Insufficient data to identify hotspots.*")
    sections.append("")

    # ── §16.10 Appendix ──
    sections.append("## 10. Appendix\n")

    # A. Bill-Level Data Register
    sections.append("### A. Bill-Level Activity Data Register\n")
    if data["bill_register"]:
        sections.append("| Bill ID | Date | Utility Type | Consumption | Unit | Cost | kg CO₂e | Scope |")
        sections.append("|---------|------|-------------|-------------|------|------|---------|-------|")
        for b in data["bill_register"]:
            sections.append(
                f"| {b['bill_id']} | {b['date']} | {b['utility_type']} | "
                f"{b['consumption']} | {b['unit']} | {b['cost']} | {b['co2e_kg']} | {b['scope']} |"
            )
    else:
        sections.append("*No bill-level data available for this period.*")
    sections.append("")

    # B. Emission Factor Reference
    sections.append("### B. Emission Factor Reference Table\n")
    sections.append("| Utility Type | Scope | Category | Emission Factor | Source |")
    sections.append("|-------------|-------|----------|----------------|--------|")
    for ef in EMISSION_FACTORS:
        sections.append(
            f"| {ef['utility_type']} | {ef['scope']} | {ef['category']} | "
            f"{ef['factor']} | {ef['source']} |"
        )
    sections.append("")
    sections.append("*Global Warming Potentials: IPCC Fifth Assessment Report (AR5), 100-year timescale.*")
    sections.append("")
    sections.append("---")
    sections.append(f"*Report generated by Carbon Auditor Platform on "
                    f"{datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. "
                    f"All calculations follow the GHG Protocol Corporate Accounting and Reporting Standard.*")

    return "\n".join(sections)


# ─── LLM Narrative Prompt (§16.1, §16.2, §16.8, §16.9) ────────────────────

def build_narrative_prompt(
    company_name: str,
    start_date: str,
    end_date: str,
    data: Dict[str, Any],
) -> str:
    """
    Builds a prompt for the LLM to generate ONLY the narrative sections.
    All numbers are pre-computed and provided — the LLM must NOT invent any.
    """
    # Build a data summary for the LLM
    scope_summary = "\n".join(
        f"  - {s['scope']} ({s['category']}): {s['kg']} kg CO₂e ({s['pct']}%)"
        for s in data["scope_breakdown"]
    )
    utility_summary = "\n".join(
        f"  - {u['utility_type']}: {u['kg']} kg CO₂e ({u['pct']}%)"
        for u in data["utility_breakdown"]
    )
    hotspot_summary = "\n".join(
        f"  - #{i+1}: {h['utility_type']} at {h['kg']} kg CO₂e ({h['pct']}%)"
        for i, h in enumerate(data["hotspots"])
    )

    prompt = f"""You are writing sections of a professional carbon emissions sustainability report for "{company_name}".
Reporting period: {start_date} to {end_date}.

CRITICAL RULES:
- Use ONLY the numbers provided below. Do NOT invent, estimate, or calculate any figure.
- Every CO₂e number you mention MUST exactly match one of the numbers listed below.
- Write in professional, third-person tone suitable for a corporate ESG report.

=== PRE-COMPUTED DATA (use ONLY these numbers) ===

Total Emissions: {data['total_kg']} kg CO₂e ({data['total_tonnes']} metric tons CO₂e)
Number of bills processed: {data['num_bills']}

Scope Breakdown:
{scope_summary}

Utility Type Breakdown:
{utility_summary}

Top Emission Hotspots:
{hotspot_summary}

Emission Factors Used:
  - Electricity: 0.385 kg CO₂e / kWh (US EPA National Average)
  - Natural Gas: 5.3 kg CO₂e / Therm (GHG Protocol Default)
  - Water: 0.344 kg CO₂e / 1000 Gallons (GHG Protocol Default)

=== SECTIONS TO WRITE ===

Write exactly these 4 sections in Markdown. Use ## headers. Be concise but professional.

## 1. Executive Summary
Write a one-paragraph plain-language summary stating:
- The total emissions for the period ({data['total_kg']} kg CO₂e / {data['total_tonnes']} metric tons)
- The single biggest contributor to the footprint (from the hotspot data above)
- A brief characterization of the organization's carbon profile

## 2. Reporting Boundary & Methodology
Write a section covering:
- Organizational boundary: operational control approach, single-site entity
- Operational boundary: Scope 1 (Natural Gas — stationary combustion), Scope 2 (Electricity — purchased), Scope 3 (Water — purchased goods & services)
- Methodology: "Emissions calculated per the GHG Protocol Corporate Accounting and Reporting Standard"
- Emission factors: reference the three factors listed above with their sources
- Data sources: all consumption data extracted via AI-powered OCR from uploaded utility bills

## 8. Reduction Recommendations
Write 3-5 concrete, prioritized recommendations tied DIRECTLY to the hotspot data above. For each recommendation state:
- WHAT to do
- WHY (tied to the specific hotspot number/percentage)
- ROUGH expected impact (qualitative, e.g., "would reduce the largest Scope 2 line item")
Categories to draw from: energy efficiency, renewable procurement (RECs), operational changes, supplier engagement, SBTi target-setting.
Do NOT invent any specific percentage reduction numbers.

## 9. Data Quality & Limitations
Write a brief section covering:
- All data in this report was extracted via AI-powered OCR from uploaded utility bills
- US national average grid emission factors were used (location-specific factors not yet applied)
- Only three utility types are currently tracked (Electricity, Natural Gas, Water)
- Market-based Scope 2 accounting not yet available (location-based only)
- Recommend third-party verification for formal compliance submissions
"""
    return prompt


# ─── Guardrail Validation ──────────────────────────────────────────────────

def validate_report_numbers(report_text: str, data: Dict[str, Any]) -> bool:
    """
    Validates that any numeric CO₂e-looking value in the LLM output
    was actually present in the pre-computed data.
    """
    allowed = set()

    # Add all known numbers
    allowed.add(str(data["total_kg"]))
    allowed.add(str(data["total_tonnes"]))

    total_kg_int = int(data["total_kg"]) if data["total_kg"] == int(data["total_kg"]) else None
    if total_kg_int is not None:
        allowed.add(str(total_kg_int))

    for s in data["scope_breakdown"]:
        allowed.add(str(s["kg"]))
        allowed.add(str(s["tonnes"]))
        allowed.add(str(s["pct"]))
        if s["kg"] == int(s["kg"]):
            allowed.add(str(int(s["kg"])))

    for u in data["utility_breakdown"]:
        allowed.add(str(u["kg"]))
        allowed.add(str(u["tonnes"]))
        allowed.add(str(u["pct"]))
        if u["kg"] == int(u["kg"]):
            allowed.add(str(int(u["kg"])))

    for b in data["bill_register"]:
        allowed.add(str(b["co2e_kg"]))
        allowed.add(str(b["consumption"]))

    # Known emission factors
    allowed.update(["0.385", "5.3", "0.344", "1000", "100"])

    # Allow small integers (section numbers, counts, etc.)
    for i in range(101):
        allowed.add(str(i))

    # Find CO₂e-looking numbers in the text
    co2e_numbers = set(
        re.findall(
            r"\b(\d+(?:\.\d+)?)\s*(?:kg\s*CO[₂2]e|metric\s*ton|tonne|t\s*CO[₂2]e|CO[₂2]e)",
            report_text,
            re.IGNORECASE,
        )
    )

    unexpected = co2e_numbers - allowed
    if unexpected:
        raise ReportGuardrailError(f"Fabricated numbers detected: {unexpected}")

    return True


# ─── Main Entry Points ─────────────────────────────────────────────────────

async def generate_report_content(
    company_name: str,
    start_date: str,
    end_date: str,
    emissions: List[Dict[str, Any]],
    bills: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Generates the full report content as Markdown.
    Deterministic sections are built in Python.
    Narrative sections are generated by the LLM with strict guardrails.
    """
    # 1. Pre-compute all numbers
    data = precompute_report_data(emissions, bills)

    # 2. Build the LLM narrative prompt
    prompt = build_narrative_prompt(company_name, start_date, end_date, data)

    # 3. Generate narrative with guardrail retries
    max_retries = 2
    narrative_text = ""
    for attempt in range(max_retries):
        narrative_text = await llm.generate_content(prompt)
        try:
            validate_report_numbers(narrative_text, data)
            break
        except ReportGuardrailError as e:
            if attempt == max_retries - 1:
                # On final failure, use a safe fallback narrative
                narrative_text = _build_fallback_narrative(company_name, start_date, end_date, data)
                break

    # 4. Build deterministic sections
    deterministic_text = build_deterministic_sections(company_name, start_date, end_date, data)

    # 5. Assemble the full report
    full_report = f"""# Carbon Emissions Report: {company_name}

**Reporting Period:** {start_date} to {end_date}
**Generated:** {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
**Standard:** GHG Protocol Corporate Accounting and Reporting Standard

---

{narrative_text}

---

{deterministic_text}
"""
    return full_report


def _build_fallback_narrative(
    company_name: str, start_date: str, end_date: str, data: Dict[str, Any]
) -> str:
    """Fallback narrative if the LLM fails guardrails twice."""
    biggest = data["hotspots"][0] if data["hotspots"] else {"utility_type": "N/A", "kg": 0, "pct": 0}

    return f"""## 1. Executive Summary

During the reporting period {start_date} to {end_date}, {company_name} recorded total greenhouse gas emissions of {data['total_kg']} kg CO₂e ({data['total_tonnes']} metric tons CO₂e). The largest contributor to the organization's carbon footprint was {biggest['utility_type']}, accounting for {biggest['pct']}% of total emissions at {biggest['kg']} kg CO₂e.

## 2. Reporting Boundary & Methodology

**Organizational Boundary:** This report covers {company_name} under the operational control consolidation approach.

**Operational Boundary:** The inventory includes Scope 1 (direct emissions from natural gas combustion), Scope 2 (indirect emissions from purchased electricity), and Scope 3 (indirect emissions from water consumption, classified under Purchased Goods & Services).

**Methodology:** Emissions were calculated per the GHG Protocol Corporate Accounting and Reporting Standard using the following emission factors:
- Electricity: 0.385 kg CO₂e / kWh (US EPA National Average)
- Natural Gas: 5.3 kg CO₂e / Therm (GHG Protocol Default)
- Water: 0.344 kg CO₂e / 1000 Gallons (GHG Protocol Default)

**Data Sources:** All consumption data was extracted via AI-powered OCR from uploaded utility bills.

## 8. Reduction Recommendations

Based on the emission hotspot analysis, the following actions are recommended:

1. **Review {biggest['utility_type']} consumption** — As the largest emission source at {biggest['pct']}% of total emissions, prioritizing efficiency improvements in this area would yield the greatest impact.
2. **Consider renewable energy procurement** — Purchasing Renewable Energy Certificates (RECs) or switching to a certified green tariff could reduce Scope 2 emissions.
3. **Establish reduction targets** — Align future goals with the Science Based Targets initiative (SBTi) framework for credible, measurable decarbonization.

## 9. Data Quality & Limitations

- All consumption data in this report was extracted via AI-powered OCR from uploaded utility bills.
- US national average grid emission factors were used; location-specific grid factors have not yet been applied.
- Only three utility types are currently tracked: Electricity, Natural Gas, and Water.
- Market-based Scope 2 accounting is not yet available; all Scope 2 figures use the location-based method.
- Third-party verification is recommended before using this report for formal compliance submissions.
"""


def generate_pdf(report_text: str, company_name: str) -> bytes:
    """Renders the Markdown report to PDF using markdown-pdf."""
    from markdown_pdf import MarkdownPdf, Section
    import tempfile
    import os

    pdf = MarkdownPdf(toc_level=2)
    pdf.meta["title"] = f"Carbon Emissions Report: {company_name}"
    pdf.meta["author"] = "Carbon Auditor Platform"

    pdf.add_section(Section(report_text))

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp_path = tmp.name

    try:
        pdf.save(tmp_path)
        with open(tmp_path, "rb") as f:
            pdf_bytes = f.read()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return pdf_bytes
