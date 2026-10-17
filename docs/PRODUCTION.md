# Career Intelligence — Production Deployment Guide

**CODE YUDH | Smart India Hackathon 2026**  
**Version:** 1.0.0  
**Target Environment:** Production Cloud (Kubernetes, AWS ECS, Docker Compose, or Bare-Metal Linux)

---

## 1. Production Architecture Overview

```
[ Client Browser / Mobile Web ]
               │
               ▼  HTTPS (Port 443 / TLS Termination)
   [ Reverse Proxy: Nginx / Cloudflare / Caddy ]
          │                           │
          ▼                           ▼
[ Next.js Frontend (Port 3000) ]     [ FastAPI Backend (Port 8000) ]
  • Node.js 20 Alpine                  • Uvicorn (4 Workers)
  • Non-root user 'nextjs'             • Non-root user 'appuser'
  • Health probe: /api/health          • Health probe: /health, /api/v1/health
                                              │
                                              ▼
                               [ PostgreSQL 16 (Port 5432) ]
                                 • Alembic Migrations (to head)
                                 • Canonical Taxonomy Reference
```

---

## 2. Production Checklist & Guarantees

| Requirement | Production Verification | Status |
| :--- | :--- | :---: |
| **No Committed Secrets** | Git tracking ignores all `.env`, `.env.*`, and `*.db` files. Only `.env.example` templates exist. | **ENFORCED** |
| **Mandatory Secrets from Env** | In `ENVIRONMENT=production`, backend fails fast if `SECRET_KEY` is default, weak, or $<32$ characters. | **ENFORCED** |
| **Debug Mode Disabled** | `DEBUG=false` required in production. Startup script & Pydantic validator abort if `DEBUG=true`. | **ENFORCED** |
| **Interactive Docs Hidden** | Interactive Swagger `/docs` and `/redoc` are disabled in production by default (`ENABLE_DOCS=false`). | **ENFORCED** |
| **CORS Restricted** | Wildcard `*` CORS origins are prohibited in production. Explicit domain whitelist required. | **ENFORCED** |
| **Configurable API Endpoints** | Frontend consumes `NEXT_PUBLIC_API_URL`; Backend binds configurable `BACKEND_HOST` and `BACKEND_PORT`. | **ENFORCED** |
| **Explicit Migrations** | Dedicated runner `backend/scripts/migrate.py` executes Alembic revisions up to `head`. | **ENFORCED** |
| **Seed / Demo Data Separation** | Canonical reference data (`backend/scripts/seed_production.py`) is decoupled from demo data. Zero mock candidates in production. | **ENFORCED** |
| **Least-Privilege Containers** | Docker containers run under dedicated non-root users (`nextjs` UID 1001, `appuser` UID 1001). | **ENFORCED** |
| **Container Health Probes** | Automated healthchecks verify both HTTP availability and relational database connectivity. | **ENFORCED** |

---

## 3. Environment Configuration

Copy the template to your deployment environment:
```bash
cp .env.example .env.production
```

### Essential Production Variables

```ini
# Environment Mode
ENVIRONMENT=production
DEBUG=false
ENABLE_DOCS=false

# Security (Generate via: openssl rand -hex 32)
SECRET_KEY=94c8b201a09d3b73e5bf7e82845c8be92389148d56b02a77918d3ef71e6ac5a4

# Server Binding
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_WORKERS=4
PORT=3000
HOSTNAME=0.0.0.0

# CORS Whitelist (Explicit domains only - NO wildcards)
CORS_ORIGINS=https://careerintel.gov.in,https://app.careerintel.gov.in

# Production Database (PostgreSQL 15+)
DATABASE_URL=postgresql://career_admin:SecureDatabasePassword2026!@postgres:5432/career_intelligence

# Frontend API Connection (Public HTTPS URL reached by clients)
NEXT_PUBLIC_API_URL=https://api.careerintel.gov.in
```

---

## 4. Database Setup & Initialization

### 4.1 Schema Migration
Database schema migrations are managed through Alembic. Run explicitly before starting app workers:
```bash
# Via Python runner
python3 backend/scripts/migrate.py

# Or via Alembic directly
cd backend
alembic -c alembic.ini upgrade head
```

### 4.2 Canonical Reference Seeding
Production relies on authoritative reference data (standard skills, benchmark career roles, course catalogs, career pathways). 

> **Important:** Run `seed_production.py`, which guarantees that **no synthetic candidates, mock passwords, or sample jobs** are written to the database.

```bash
python3 backend/scripts/seed_production.py
```

### 4.3 Staging / Demo Seeding (Non-Production Only)
For staging evaluations or sandbox environments only:
```bash
python3 backend/scripts/seed_demo.py
```

---

## 5. Docker Production Orchestration

### 5.1 Docker Compose Deployment
Launch the complete production stack (PostgreSQL + FastAPI Backend + Next.js Frontend) using `docker-compose.production.yml`:

```bash
# 1. Export required environment variables
export POSTGRES_PASSWORD="SecureDatabasePassword2026!"
export SECRET_KEY="$(openssl rand -hex 32)"
export NEXT_PUBLIC_API_URL="https://api.yourdomain.com"
export CORS_ORIGINS="https://yourdomain.com"

# 2. Build and start containers with health dependencies
docker compose -f docker-compose.production.yml up -d --build

# 3. Check health and service status
docker compose -f docker-compose.production.yml ps
```

### 5.2 Container Verification
```bash
# Check Backend Health
curl -s http://localhost:8000/health | jq .

# Check Frontend Health
curl -s http://localhost:3000/api/health | jq .
```

---

## 6. Local & Bare-Metal Production Build

To run an optimized production build on bare-metal or standalone virtual machines:

### Step 1: Build Frontend Assets
```bash
cd frontend
export NEXT_PUBLIC_API_URL="https://api.yourdomain.com"
npm ci
npm run build
```

### Step 2: Prepare Backend Virtual Environment
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt
```

### Step 3: Run Database Migration & Canonical Seeding
```bash
python3 scripts/migrate.py
python3 scripts/seed_production.py
```

### Step 4: Execute Production Startup Script
```bash
# Launches Uvicorn with multi-worker concurrency and security pre-flight checks:
./scripts/start_production.sh
```

### Step 5: Start Frontend Production Server
```bash
cd frontend
./scripts/start_production.sh
```

---

## 7. Health Monitoring & Probes

| Component | Endpoint | Protocol | Expected Response | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Backend API** | `/health` | HTTP GET | `{"status": "healthy", "database": "connected"}` | Root service & DB connectivity probe |
| **Backend API v1** | `/api/v1/health` | HTTP GET | `{"status": "healthy", "service": "Career Intelligence API"}` | Versioned API subsystem check |
| **Frontend Web** | `/api/health` | HTTP GET | `{"status": "healthy", "service": "career-intelligence-frontend"}` | Next.js server & runtime check |
| **CLI Probe** | `backend/scripts/healthcheck.py` | CLI / Python | Exit code `0` | Used by Docker & Kubernetes liveness probes |

---

## 8. Security & Operational Policies

1. **In-Memory Resume Ingestion**: Resumes are parsed entirely within memory streams (`PyMuPDF` / `python-docx`) and never persisted to filesystem or external object stores unless explicit candidate consent is granted.
2. **PII Masking**: Secrets, tokens, API keys, and sensitive contact numbers are scrubbed prior to log serialization via `app/core/logging_security.py`.
3. **Response Compression**: GZip middleware automatically compresses JSON payloads exceeding 1 KB, reducing mobile bandwidth consumption.
4. **Rate Limiting**: Critical endpoints (`/documents/upload`, `/recruiter/parse-jd`) are protected against denial-of-service abuse via the sliding-window rate limiter.
5. **No Hallucination ATS**: All matching scores are generated by transparent, deterministic formulas. The system does not delegate hiring or rejection decisions to autonomous LLMs without explainable evidence.
