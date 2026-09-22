from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1 import bills, emissions, chat, reports

app = FastAPI(title="Carbon Auditor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint — returns 200 when the service is up."""
    return JSONResponse({"status": "ok"})


app.include_router(bills.router, prefix="/api/v1/bills", tags=["Bills"])
app.include_router(emissions.router, prefix="/api/v1/emissions", tags=["Emissions"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(reports.router, prefix="/api/v1", tags=["Reports"])
