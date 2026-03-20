# 🚀 Tangent — JIT Multi-Agent System

**Tangent** is a Just-In-Time (JIT) multi-agent orchestration framework. A Meta-Agent compiles high-level objectives into a dependency graph of ephemeral sub-agents. State is persisted in PostgreSQL; the event bus runs on Redis.

The project is structured for easy deployment on **Railway**:

- **`backend/`** — FastAPI server (Python) agent engine.
- **`frontend/`** — React/Vite UI for interacting with workflows.

---

## ⚡ Deployment to Railway (Recommended)

Tangent is optimized for Railway. Follow these steps for a 2-minute deployment:

### 1. Create a New Railway Project
- Connect your GitHub repo to Railway.
- Railway will detect the `backend/` and `frontend/` directories.

### 2. Add Infrastructure
- Click **"+ New"** → **Postgres** (provides `DATABASE_URL`)
- Click **"+ New"** → **Redis** (provides `REDIS_URL`)

### 3. Configure Internal Services

#### **Backend Service** (Point to `/backend`)
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Variables**:
  - `DATABASE_URL` (automatic)
  - `REDIS_URL` (automatic)
  - `GEMINI_API_KEY=...` (get from [Google AI Studio](https://aistudio.google.com/apikey))
  - `API_KEY=nagent-dev-key`

#### **Frontend Service** (Point to `/frontend`)
- **Build Command**: `npm install && npm run build`
- **Start Command**: `npx serve -s dist -l $PORT`
- **Variables**:
  - `VITE_API_URL=https://your-backend-url.up.railway.app`
  - `VITE_WS_URL=wss://your-backend-url.up.railway.app`
  - `VITE_API_KEY=nagent-dev-key`

---

## 🛠️ Local Development

### 1. Simple (Docker Compose)
Start the entire stack (Postgres, Redis, Backend, Frontend) with one command:
```bash
docker compose up --build
```
- UI: `http://localhost:3000`
- API: `http://localhost:8000`

### 2. Manual Setup
If you prefer running without Docker:

#### **Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Ensure Postgres/Redis are running localy, then:
uvicorn main:app --reload --port 8000
```

#### **Frontend**
```bash
cd frontend
npm install
npm run dev
```

---

## 📂 Project Structure

```
tangent/
├── backend/            # FastAPI & Agent Engine
│   ├── main.py         # Entrypoint
│   ├── meta.py         # Architect Agent
│   ├── requirements.txt
│   └── Dockerfile      # Railway Backend Spec
├── frontend/           # React/Vite UI
│   ├── src/
│   ├── package.json
│   └── Dockerfile      # Railway Frontend Spec
└── Dockerfile          # Combined Multi-stage Build (alternative)
```

---

## 🔒 Security
The `API_KEY` (default: `nagent-dev-key`) is used to authenticate the frontend's connection to your backend. In production, change this to a long random string.
LLM provider keys (Gemini, OpenAI, etc.) are **never** exposed to the frontend.
