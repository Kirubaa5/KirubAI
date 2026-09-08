# Deployment Architecture — KirubAI

## 1. Deployment Targets

| Component | Platform | Tier |
|-----------|----------|------|
| Frontend | Vercel | Free |
| Backend | Render | Free |
| Database | Supabase | Free |

## 2. Architecture

```
┌───────────────┐
│   Browser     │
└───────┬───────┘
        │ HTTPS
        ▼
┌───────────────┐        ┌───────────────────┐
│   Vercel      │        │   LLM Provider    │
│   (Frontend)  │        │   (OpenAI /       │
│   React SPA   │        │    Gemini /       │
└───────┬───────┘        │    OpenRouter)    │
        │ HTTPS           └───────▲───────────┘
        ▼                         │
┌───────────────┐                 │
│   Render      │─────────────────┘
│   (Backend)   │
│   FastAPI     │
└───────┬───────┘
        │ SSL
        ▼
┌───────────────┐
│   Supabase    │
│   PostgreSQL  │
└───────────────┘
```

## 3. Local Development

### Docker Compose
```yaml
services:
  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    volumes: ["./frontend:/app"]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    volumes: ["./backend:/app"]
    environment:
      - DATABASE_URL=postgresql://...
    depends_on: [db]

  db:
    image: postgres:16
    ports: ["5432:5432"]
    environment:
      - POSTGRES_DB=kirubai
      - POSTGRES_USER=kirubai
      - POSTGRES_PASSWORD=kirubai
    volumes: ["pgdata:/var/lib/postgresql/data"]

volumes:
  pgdata:
```

### Development Workflow
```bash
docker compose up          # Start all services
docker compose up backend  # Start backend only
docker compose down        # Stop all
```

## 4. Frontend Deployment (Vercel)

### Configuration
- Framework: Vite
- Build command: `npm run build`
- Output directory: `dist`
- Node version: 20

### Environment Variables (Vercel)
```
VITE_API_URL=https://kirubai-api.onrender.com/api/v1
```

### Deployment
- Auto-deploy on push to `main`
- Preview deployments on PRs

## 5. Backend Deployment (Render)

### Configuration
- Runtime: Python 3.12
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health check: `/health`

### Environment Variables (Render)
```
DATABASE_URL=postgresql://...  (from Supabase)
JWT_SECRET_KEY=<generated>
LLM_PROVIDER=openai
OPENAI_API_KEY=<key>
CORS_ORIGINS=https://kirubai.vercel.app
DEBUG=false
```

### Render Free Tier Notes
- Spins down after 15 min of inactivity
- First request after spin-up takes ~30 seconds
- Acceptable for development/portfolio project

## 6. Database (Supabase)

### Configuration
- PostgreSQL 15
- Connection pooling via Supabase
- SSL enforced

### Connection String
```
postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
```

### Migrations
```bash
# Run migrations before deployment
alembic upgrade head
```

### Supabase Free Tier
- 500 MB database
- 2 GB bandwidth/month
- Sufficient for portfolio/demo

## 7. Environment Configuration

### Three Environments

| Environment | Database | LLM | Debug |
|------------|----------|-----|-------|
| Development | Local PostgreSQL (Docker) | Mock | true |
| Testing | SQLite in-memory | Mock | true |
| Production | Supabase PostgreSQL | OpenAI/Gemini | false |

### Configuration Loading
```python
# backend/config.py
import os

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://kirubai:kirubai@localhost:5432/kirubai")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
```

## 8. CI/CD

### GitHub Actions (future)
```
Push to main →
  Backend: lint → typecheck → test → deploy to Render
  Frontend: lint → typecheck → test → build → deploy to Vercel
```

For the initial project, manual deployment via platform auto-deploy is sufficient.

## 9. Monitoring (Minimal)

- Render: built-in logs and metrics
- Vercel: built-in analytics
- Supabase: built-in database metrics
- Application: structured logging to stdout

## 10. Cost Summary

| Service | Monthly Cost |
|---------|-------------|
| Vercel | $0 |
| Render | $0 |
| Supabase | $0 |
| LLM API | Usage-based (~$1-5 for demo) |
| **Total** | **~$1-5/month** |
