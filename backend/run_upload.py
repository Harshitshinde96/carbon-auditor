"""Script to test uploading a bill and monitoring the processing status."""
import requests
import time
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"
PDF_PATH = r"D:\01_Web Development\04_Projects\01_My Bulids\Carbon-Auditor\20260921071434-094020055507.pdf"

print("1. Uploading bill...")
try:
    with open(PDF_PATH, "rb") as f:
        files = {"bill_file": ("test_bill.pdf", f, "application/pdf")}
        response = requests.post(f"{BASE_URL}/bills/upload", files=files)
except requests.exceptions.ConnectionError:
    print("ERROR: Is the local FastAPI server running on port 8000?")
    sys.exit(1)

if response.status_code != 202:
    print(f"Failed to upload: {response.status_code} - {response.text}")
    sys.exit(1)

data = response.json()
bill_id = data["data"]["bill_id"]
print(f"Upload successful. Bill ID: {bill_id}")

print("\n2. Polling for processing status...")
max_attempts = 20
for attempt in range(max_attempts):
    time.sleep(2)
    resp = requests.get(f"{BASE_URL}/bills/{bill_id}")
    if resp.status_code != 200:
        print(f"Failed to fetch bill: {resp.status_code} - {resp.text}")
        continue
    
    bill_data = resp.json()["data"]
    status = bill_data.get("status")
    print(f"Attempt {attempt + 1}: Status = {status}")
    
    if status == "COMPLETED":
        print("\n=== SUCCESS! Extracted Data ===")
        print(json.dumps(bill_data.get("extracted_data"), indent=2))
        print("\n=== Calculated Emissions ===")
        print(json.dumps(bill_data.get("emissions"), indent=2))
        break
    elif status.startswith("FAILED"):
        print("\n=== PROCESSING FAILED ===")
        print(bill_data.get("error_message"))
        break
else:
    print("Timed out waiting for processing to complete.")
