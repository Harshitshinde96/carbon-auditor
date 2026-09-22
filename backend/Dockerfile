FROM python:3.12-slim AS base

WORKDIR /app

# Install system dependencies needed by markitdown/pdf tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Dependency stage ──────────────────────────────────────────────────────────
FROM base AS deps

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# ── Final stage ───────────────────────────────────────────────────────────────
FROM deps AS final

COPY . .

# Health check — Docker will mark container unhealthy if this fails
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Use gunicorn with uvicorn workers as specified in TECH_STACK.md §11
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", \
     "--workers", "1", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "app.main:app"]
