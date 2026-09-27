#!/usr/bin/env bash
set -e

# Start demo script for ZeroCaffeine Studio PoC
# - creates a virtualenv (if not present)
# - installs minimal Python deps
# - starts backend (FastAPI) on port 8000
# - serves frontend folder on port 8080 using python's http.server

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE_DIR"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip >/dev/null
pip install fastapi uvicorn pydantic >/dev/null

# Start backend
echo "Starting backend on http://localhost:8000 ..."
uvicorn backend.app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Serve frontend
echo "Serving frontend on http://localhost:8080/index.html ..."
( cd frontend && python3 -m http.server 8080 ) &
FRONT_PID=$!

echo "Demo started. Backend PID=${BACKEND_PID}, Frontend PID=${FRONT_PID}"

echo "Open the frontend at: http://localhost:8080/index.html"
echo "Open the OpenAPI docs at: http://localhost:8000/docs"

# Wait for background processes
wait $BACKEND_PID $FRONT_PID
