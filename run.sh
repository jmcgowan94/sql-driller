#!/bin/bash
echo "==> cd into backend/ (where the Python app lives)"
cd "$(dirname "$0")/backend"

echo "==> source .venv/bin/activate (activate the Python virtual environment)"
source .venv/bin/activate

echo ""
echo "Starting SQL Driller..."
echo "Open your browser to: http://localhost:8000"
echo "(Press Ctrl+C here to stop it when you're done)"
echo ""

echo "==> uvicorn app.main:app --port 8000 (start the FastAPI server)"
uvicorn app.main:app --port 8000
