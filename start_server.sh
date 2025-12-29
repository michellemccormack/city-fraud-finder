#!/bin/bash
cd "$(dirname "$0")"

# Always kill any existing server first
echo "Stopping any existing server..."
pkill -9 -f "uvicorn" 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 2

# Start the server
echo "Starting server..."
source .venv/bin/activate
python3 -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
