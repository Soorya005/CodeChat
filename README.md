# CodeChat — AI-Powered Repository Intelligence Platform

CodeChat is a full-stack AI repository intelligence platform that helps developers understand, navigate, and interact with software codebases using Retrieval-Augmented Generation (RAG).

Unlike generic AI chatbots, CodeChat performs syntax-aware code parsing, semantic retrieval, and repository-specific contextual reasoning to provide accurate answers about uploaded repositories.

Built with a modern React + FastAPI architecture, the platform supports intelligent repository ingestion, vector-based semantic search, authentication, persistent chat history, and automated repository re-indexing workflows.

---

# Features

- AI-powered repository chat
- Syntax-aware code chunking using AST + Tree-sitter
- Semantic vector search using FAISS
- Repository-specific contextual responses
- Authentication and user-based chat history
- Multi-language repository support
- CI/CD-assisted automatic re-indexing
- Groq-powered ultra-fast LLM responses
- Modular RAG pipeline architecture
- Docker-ready deployment support

---

# Architecture

```text
Repository → Ingestion → AST/Tree-sitter Chunking
           → Embeddings → FAISS Vector Store
           → Semantic Retrieval → LLM Response
           → React Chat Interface
```

---

# Tech Stack

## Frontend
- React
- Next.js
- TailwindCSS

## Backend
- FastAPI
- Python
- JWT Authentication

## AI / RAG
- FAISS
- Sentence Transformers
- AST Parsing
- Tree-sitter
- Groq API

## Database
- PostgreSQL / SQLite

---

# Prerequisites

- Python 3.12+
- Node.js 18+
- Git

---

# 1. Clone Repository

```bash
git clone https://github.com/Soorya005/cclatest.git
cd cclatest
```

---

# 2. Get Groq API Key

CodeChat uses Groq Cloud for high-speed inference.

1. Visit:
   https://console.groq.com

2. Create a free API key

3. Save the key for backend configuration

---

# 3. Backend Setup

```bash
cd backend

python3 -m venv .venv
```

## Activate Virtual Environment

### Linux/macOS
```bash
source .venv/bin/activate
```

### Windows PowerShell
```powershell
.venv\Scripts\activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Configure Environment Variables

```bash
cp .env.example .env
```

Edit `backend/.env`:

```env
GROQ_API_KEY=your_groq_api_key
JWT_SECRET_KEY=change-this-in-production
```

## Initialize Database

```bash
python create_tables.py
```

## Start Backend Server

```bash
uvicorn app.main:app --reload
```

Backend runs at:

```text
http://127.0.0.1:8000
```

---

# 4. Frontend Setup

Open another terminal:

```bash
cd frontend

npm install
```

## Configure Frontend Environment

```bash
cp .env.example .env.local
```

Ensure:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

## Start Frontend

```bash
npm run dev
```

Frontend runs at:

```text
http://localhost:3000
```

---

# 5. First Run

1. Open:
   ```text
   http://localhost:3000
   ```

2. Register an account

3. Login

4. Add a GitHub repository

5. Start indexing

6. Ask repository-specific questions

---

# Repository Sync & CI/CD Integration

CodeChat supports automatic repository re-indexing through GitHub Actions.

Every push to the target repository can automatically trigger background re-indexing.

---

# Sync Workflow Overview

```text
GitHub Push
    ↓
GitHub Actions
    ↓
CodeChat Sync Endpoint
    ↓
Repository Re-indexing
    ↓
Updated Vector Database
```

---

# Step 1 — Expose Backend Using ngrok

Run backend:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

In another terminal:

```bash
ngrok http 8000
```

Copy the generated public URL:

```text
https://xxxxx.ngrok-free.app
```

---

# Step 2 — Add Repository in CodeChat

After logging into CodeChat:

- Add repository URL
- Backend returns:
  - `repository_id`
  - `sync_api_key`

These are required for GitHub Actions integration.

---

# Step 3 — Configure GitHub Secrets

In target repository:

## Add GitHub Secrets

```text
CODECHAT_API_KEY
```

## Add GitHub Variables

```text
CODECHAT_URL
CODECHAT_REPO_ID
```

---

# Step 4 — Enable Workflow

Use:

```text
.github/workflows/codechat-sync.yml
```

Triggers:
- Push to `main`
- Manual workflow execution

---

# Troubleshooting

## Frontend Cannot Connect to Backend

Check:
- Backend running on port 8000
- Correct `NEXT_PUBLIC_API_URL`
- No firewall/proxy blocking

---

## GROQ_API_KEY Error

Get API key from:

https://console.groq.com

Update:

```text
backend/.env
```

---

## Database Errors

Run:

```bash
python create_tables.py
```

---

## Windows Issues

Use:

```powershell
.\run.ps1
```

instead of Linux shell commands.

---

# Environment Variables

| Variable | Required | Description |
|---|---|---|
| GROQ_API_KEY | Yes | Groq API key |
| JWT_SECRET_KEY | Yes | JWT signing secret |
| DATABASE_URL | No | Database connection URL |
| NEXT_PUBLIC_API_URL | Yes | Backend API URL |

---

# Project Structure

```text
codechat/
│
├── backend/
├── frontend/
├── .github/workflows/
├── docs/
├── examples/
│
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── ROADMAP.md
├── .env.example
│
├── run.sh
├── run.ps1
└── docker-compose.yml
```

---

# Future Scope

- Dependency graph visualization
- Repository architecture mapping
- Agentic repository exploration
- Vulnerability-aware code analysis
- Multi-repository semantic search
- MCP/tool integration support
- Team collaboration features

---

# Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Open a pull request

Please follow clean coding practices and proper documentation standards.

---

# License

This project is licensed under the MIT License.
