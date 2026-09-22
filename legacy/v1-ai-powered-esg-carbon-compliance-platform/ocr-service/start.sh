#!/usr/bin/env bash
# Start script for the OCR Microservice

# Ensure uvicorn is found
export PATH=$PATH:~/.local/bin

# Run uvicorn on port 10000 (Render default for web services)
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}
