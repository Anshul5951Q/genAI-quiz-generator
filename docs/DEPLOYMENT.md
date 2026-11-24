# StudySet AI — Deployment & Operations Guide

## 1. System Requirements & Architecture
StudySet AI is structured as a modern two-tier SaaS application:
- **Backend**: FastAPI (Python 3.11+) with SQLAlchemy ORM and Alembic.
- **Frontend**: React 19 + TypeScript + Vite + Tailwind CSS v4.
- **Database**: SQLite (default zero-config local) or PostgreSQL (production containerized).
- **AI Inference Engine**: Ollama (local) with Groq / Gemini cloud failover.

---

## 2. Local Development Deployment

### 2.1 Backend Setup
1. Navigate to `backend/`:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
4. Verify environment settings in `.env` (copy from `.env.example` if needed).
5. Start the FastAPI development server:
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   Backend will be active at `http://localhost:8000`. OpenAPI documentation is available at `http://localhost:8000/docs`.

### 2.2 Frontend Setup
1. Navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Start Vite dev server:
   ```bash
   npm run dev
   ```
   Frontend will be active at `http://localhost:5173`.

---

## 3. Production Docker Deployment

### 3.1 Dockerfile (Backend)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 3.2 Dockerfile (Frontend)
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 3.3 Docker Compose (`docker-compose.yml`)
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://studyset:secretpass@postgres:5432/studyset_db
      - LLM_PRIMARY_PROVIDER=ollama
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - postgres

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=studyset
      - POSTGRES_PASSWORD=secretpass
      - POSTGRES_DB=studyset_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

---

## 4. Environment Variables Reference

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///./studyset.db` |
| `SECRET_KEY` | JWT HMAC secret key | Set in `.env` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token lifetime | `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` |
| `LLM_PRIMARY_PROVIDER` | Primary inference engine (`ollama`, `groq`, `gemini`) | `ollama` |
| `OLLAMA_BASE_URL` | Local Ollama endpoint | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model identifier | `qwen2.5:3b` |
| `GROQ_API_KEY` | Groq cloud fallback key | Optional |
| `GEMINI_API_KEY` | Gemini cloud fallback key | Optional |
