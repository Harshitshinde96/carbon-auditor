import httpx
import sys


def run_smoke_tests():
    base_url = "http://localhost:8000/api/v1"

    print("1. Testing POST /auth/login")
    r1 = httpx.post(
        f"{base_url}/auth/login",
        json={"email": "user@example.com", "password": "securepassword123"},
    )
    if r1.status_code != 200:
        print(f"Auth failed: {r1.status_code}")
        sys.exit(1)

    print("2. Testing POST /bills/upload")
    files = {"bill_file": ("test.txt", b"dummy content", "text/plain")}
    # text/plain isn't allowed, let's use a dummy pdf
    files = {"bill_file": ("test.pdf", b"%PDF-1.4 dummy", "application/pdf")}
    r2 = httpx.post(f"{base_url}/bills/upload", files=files)
    if r2.status_code != 202:
        print(f"Upload failed: {r2.status_code} - {r2.text}")
        sys.exit(1)
    bill_id = r2.json()["data"]["bill_id"]

    print(f"3. Testing GET /bills/{bill_id}")
    r3 = httpx.get(f"{base_url}/bills/{bill_id}")
    if r3.status_code != 200:
        print(f"Get bill failed: {r3.status_code}")
        sys.exit(1)

    print("4. Testing GET /bills")
    r4 = httpx.get(f"{base_url}/bills/?limit=5")
    if r4.status_code != 200:
        print(f"List bills failed: {r4.status_code}")
        sys.exit(1)

    print("5. Testing GET /emissions/summary")
    r5 = httpx.get(f"{base_url}/emissions/summary")
    if r5.status_code != 200:
        print(f"Emissions summary failed: {r5.status_code}")
        sys.exit(1)

    print("6. Testing POST /chat/query")
    # This hits real Qdrant and Gemini now that the keys are in .env
    r6 = httpx.post(
        f"{base_url}/chat/query", json={"query": "What are scope 1 emissions?"}
    )
    if r6.status_code != 200:
        print(f"Chat query failed: {r6.status_code}")
        sys.exit(1)

    print("All smoke tests passed!")


if __name__ == "__main__":
    run_smoke_tests()
