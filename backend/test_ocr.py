import os
from dotenv import load_dotenv
load_dotenv("backend/.env")

from app.services.ocr_service import process_bill_ocr

try:
    res = process_bill_ocr("backend/data/ghg_protocol_docs/Quantitative Uncertainty Guidance.pdf", "test_id")
    print(res)
except Exception as e:
    print("FAILED:", e)
