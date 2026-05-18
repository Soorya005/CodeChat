# Setup Guide - Common Issues & Solutions

If you're seeing "loading error", "failed to fetch", or other errors after cloning, follow this guide.

## Required Steps (in order)

### Step 1: Get GROQ API Key ⚠️ **MUST DO FIRST**

This is the #1 cause of setup failures. CodeChat needs an LLM API key.

1. Open https://console.groq.com in your browser
2. Sign up (free) or login
3. Create an API key from the dashboard
4. Copy the key
5. **Keep it safe** - you'll paste it in step 3

### Step 2: Clone the Repository

```bash
git clone https://github.com/Soorya005/cclatest.git
cd cclatest
```

### Step 3: Backend Setup

#### Linux/Mac:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Windows (PowerShell):
```bash
cd backend
python3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Step 4: Configure Backend

```bash
cp .env.example .env
```

**Edit `backend/.env` with your API key:**

Find these lines and update them:

```env
GROQ_API_KEY=paste_your_api_key_here
JWT_SECRET_KEY=change-me-before-production
```

Save the file.

### Step 5: Initialize Database

```bash
python create_tables.py
```

(You should see: "Tables created successfully" or similar message)

### Step 6: Start Backend

```bash
uvicorn app.main:app --reload
```

Expected output:
```
Uvicorn running on http://127.0.0.1:8000
```

✅ **Leave this terminal running**

### Step 7: Setup Frontend (new terminal/tab)

From the root directory:

#### Linux/Mac:
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

#### Windows:
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Expected output:
```
▲ Next.js [version]
  - Local:        http://localhost:3000
```

✅ **Open http://localhost:3000 in your browser**

## Common Problems & Solutions

### ❌ "loading error" or spinner stuck on homepage

**Cause:** Frontend can't reach backend

**Fix:**
1. Check that backend is running: Visit http://127.0.0.1:8000 in browser
2. Check `frontend/.env.local` has:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
3. Restart frontend: Stop `npm run dev`, then run it again

---

### ❌ "failed to fetch" error in network tab

**Cause:** CORS error or backend not running

**Check:**
1. Copy this URL in browser: http://127.0.0.1:8000/docs
   - If it works ✅ backend is running
   - If it fails ❌ backend crashed or not started
2. Terminal 1: Make sure backend is still running
3. Terminal 2: Restart frontend with `npm run dev`

---

### ❌ "Invalid GROQ_API_KEY" error

**Cause:** API key not set or invalid

**Fix:**
1. Check `backend/.env` has your real key:
   ```
   GROQ_API_KEY=gsk_xxxxx...
   ```
   (Not `your_groq_api_key_here`)
2. Get a new key from https://console.groq.com
3. Copy exact key (including `gsk_` prefix)
4. Save & restart backend

---

### ❌ "No such file or directory: codechat.db"

**Cause:** Database wasn't initialized

**Fix:**
```bash
cd backend
source .venv/bin/activate  # (or .venv\Scripts\activate on Windows)
python create_tables.py
uvicorn app.main:app --reload
```

---

### ❌ "ModuleNotFoundError" when running backend

**Cause:** Dependencies not installed

**Fix:**
```bash
cd backend
source .venv/bin/activate  # (or .venv\Scripts\activate on Windows)
pip install -r requirements.txt
```

---

### ❌ npm install fails with dependency errors

**Cause:** Node version incompatibility

**Fix:**
- Check Node version: `node --version` (need 18+)
- Clean install:
  ```bash
  cd frontend
  rm -rf node_modules pnpm-lock.yaml
  npm install
  ```

---

## Quick Start Script

If you want to automate setup:

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows (PowerShell):**
```powershell
.\run.ps1
```

Then follow steps 4 & 6-7 above to set your GROQ key and start the app.

---

## Verify Everything is Working

1. Backend running: http://127.0.0.1:8000/docs ✅
2. Frontend running: http://localhost:3000 ✅
3. Can see login page ✅
4. Register → Login ✅
5. Add repository URL ✅
6. Index repository ✅
7. Ask a question ✅

---

## Still Having Issues?

Check these files:
- `backend/.env` - has your GROQ_API_KEY?
- `frontend/.env.local` - has NEXT_PUBLIC_API_URL=http://localhost:8000?
- Terminal 1 - backend running on 8000?
- Terminal 2 - frontend running on 3000?

All 4 must be ✅ yes.
