#!/bin/bash
cd "$(dirname "$0")/backend"
source .venv/bin/activate
echo ""
echo "Starting SQL Driller..."
echo "Open your browser to: http://localhost:8000"
echo "(Press Ctrl+C here to stop it when you're done)"
echo ""
uvicorn app.main:app --port 8000
