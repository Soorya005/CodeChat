# CodeChat (Backend + Frontend)

Clone and run locally with minimal setup.

## 1) Prerequisites

- Python 3.12+
- Node.js 18+
- Ollama installed

## 2) Clone

```bash
git clone https://github.com/Soorya005/cclatest.git
cd cclatest
```

## 3) Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python create_tables.py
uvicorn app.main:app --reload
```

Backend runs at: `http://127.0.0.1:8000`

## 4) Ollama setup

In a separate terminal:

```bash
ollama serve
ollama pull llama3.2:1b
```

## 5) Frontend setup

In another terminal:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Frontend runs at: `http://localhost:3000`

## 6) First run flow

1. Register and login in UI
2. Add a repository URL
3. Index repository
4. Ask questions in chat

## Notes

- Do **not** commit real `.env` files with secrets.
- Local generated files (`backend/indexes/`, `backend/codechat.db`, `.venv/`) are ignored.
