# CodeChat (Backend + Frontend)

Clone and run locally with minimal setup.
Can use api key for access cloud llms too

## 1) Prerequisites

- Python 3.12+
- Node.js 18+

## 2) ⚠️ Get GROQ API Key First (Required)

CodeChat uses Groq for instant, high-speed LLM responses. 
1. Visit [console.groq.com](https://console.groq.com)
2. Sign up and create an API key
3. Save it - you'll need it in step 4

## 3) Clone

```bash
git clone https://github.com/Soorya005/cclatest.git
cd cclatest
```

## 4) Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

**IMPORTANT: Edit `backend/.env` and replace:**
```env
GROQ_API_KEY=your_api_key_from_console.groq.com
JWT_SECRET_KEY=change-me-before-production
```

Then initialize database and start:
```bash
python create_tables.py
uvicorn app.main:app --reload
```

Backend runs at: `http://127.0.0.1:8000`

> **Migration Note for Existing Users:**
> CodeChat is now exclusively powered by Groq. Ollama and Gemini fallback support have been removed. If you are updating from a previous version, please ensure your `.env` file is updated to remove `OLLAMA_*` and `GEMINI_*` variables, and ensure `GROQ_API_KEY` is set.

## 5) Frontend Setup

In another terminal:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Frontend runs at: `http://localhost:3000`

**Note:** Make sure `NEXT_PUBLIC_API_URL=http://localhost:8000` in `.env.local` matches your backend URL.

## 6) First Run

1. Open http://localhost:3000 in your browser
2. Register and login
3. Add a repository URL
4. Index repository
5. Ask questions in chat

## 7) Troubleshooting

**"Loading error" or "failed to fetch" in frontend:**
- ✅ Is backend running? Check http://127.0.0.1:8000 in browser
- ✅ Does `.env.local` have correct `NEXT_PUBLIC_API_URL`?
- ✅ Are both running on expected ports (backend: 8000, frontend: 3000)?

**"GROQ_API_KEY" error:**
- Get a free key at https://console.groq.com
- Update `backend/.env` with your key

**"Database" errors:**
- Run `python create_tables.py` in backend/ directory

**Windows users:**
- Use `.venv\Scripts\activate` instead of `source .venv/bin/activate`
- Or run `.\run.ps1` from PowerShell in repo root

## 8) Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ Yes | Get from console.groq.com |
| `JWT_SECRET_KEY` | ✅ Yes | Change from default before production |
| `DATABASE_URL` | No | Defaults to SQLite (local database) |
| `NEXT_PUBLIC_API_URL` | ✅ Yes (frontend) | URL where backend is running |

## 7) CI/CD auto-sync to CodeChat (localhost via ngrok)

This project already supports background re-indexing through:

- `POST /repository/sync/{repo_id}?api_key=...`

Use GitHub Actions in your target repository so every push to `main` triggers this endpoint.

### Step A: Run backend and expose it with ngrok

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

In another terminal:

```bash
ngrok http 8000
```

Copy the public forwarding URL (example: `https://abc123.ngrok-free.app`).

### Step B: Get `repo_id` and `sync_api_key` from CodeChat

After login in UI, add your target repository URL.

The backend response from `POST /repository/add` includes:

- `repository_id` -> use as `CODECHAT_REPO_ID`
- `sync_api_key` -> use as `CODECHAT_API_KEY`

### Step C: Configure GitHub repository settings (target repo)

In the target GitHub repository:

- Settings -> Secrets and variables -> Actions -> **Secrets**
	- Add `CODECHAT_API_KEY` with value from `sync_api_key`
- Settings -> Secrets and variables -> Actions -> **Variables**
	- Add `CODECHAT_URL` with your ngrok URL (no trailing slash)
	- Add `CODECHAT_REPO_ID` with numeric `repository_id`

### Step D: Enable workflow in target repo

Use the workflow file at `.github/workflows/codechat-sync.yml`.

It triggers on:

- `push` to `main`
- manual run (`workflow_dispatch`)

### Step E: Validate

1. Push a small commit to `main` in target repo.
2. Confirm workflow success in GitHub Actions.
3. In CodeChat UI, check status transitions `INDEXING` -> `INDEXED`.
4. Query newly pushed code and verify updated answers.

### Important for localhost + ngrok

Each time ngrok URL changes, update GitHub Actions variable `CODECHAT_URL`.
