#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[1/4] Backend venv + deps"
cd "$ROOT_DIR/backend"
if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt

if [[ ! -f ".env" ]]; then
  cp .env.example .env
  echo "Created backend/.env from .env.example"
fi

python create_tables.py

echo "[2/4] Frontend deps"
cd "$ROOT_DIR/frontend"
npm install

if [[ ! -f ".env.local" ]]; then
  cp .env.example .env.local
  echo "Created frontend/.env.local from .env.example"
fi

echo "[3/4] Database initialization"
cd "$ROOT_DIR/backend"
source .venv/bin/activate
python create_tables.py

echo "[4/4] Setup complete!"
echo ""
echo "⚠️  IMPORTANT: Set your GROQ API Key"
echo "1. Visit: https://console.groq.com"
echo "2. Get your API key"
echo "3. Update backend/.env with: GROQ_API_KEY=your_key_here"
echo ""
echo "To start the app:"
echo "  Terminal 1: cd backend && source .venv/bin/activate && uvicorn app.main:app --reload"
echo "  Terminal 2: cd frontend && npm run dev"
echo "Run ./run.sh to start backend, frontend, and ollama checks."
