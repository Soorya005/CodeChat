#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if backend/.env has GROQ_API_KEY configured
if grep -q "GROQ_API_KEY=your_groq_api_key_here" "$ROOT_DIR/backend/.env" 2>/dev/null || ! grep -q "GROQ_API_KEY=" "$ROOT_DIR/backend/.env" 2>/dev/null; then
  echo "⚠️  ERROR: GROQ_API_KEY not configured in backend/.env"
  echo "Please set your GROQ API key from https://console.groq.com"
  exit 1
fi

echo "Starting backend on http://127.0.0.1:8000"
(
  cd "$ROOT_DIR/backend"
  source .venv/bin/activate
  uvicorn app.main:app --reload
) &
BACKEND_PID=$!

echo "Starting frontend on http://localhost:3000"
(
  cd "$ROOT_DIR/frontend"
  npm run dev
) &
FRONTEND_PID=$!

cleanup() {
  echo "Stopping services..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "Press Ctrl+C to stop both"
wait
