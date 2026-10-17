# Career Intelligence

> **MATCH → GAP → LEARN → GROW**  
> *An explainable AI talent–job matching ecosystem for India.*  
> **Smart India Hackathon 2026 — Build for Bharat 2.0** | **Team Move-On Coders**

---

## 📌 Problem & Vision
India faces a severe talent-job disconnect: recent NITI Aayog analysis reports **1.86 crore applicants for 55,000 public posts (~340:1 ratio)** alongside high graduate underemployment. Black-box ATS filters reject qualified candidates without explanation or recourse. 

**Career Intelligence** turns unstructured resumes and job descriptions into explainable skill maps, transparent mathematical match scores, prerequisite-ordered gap analyses, and actionable learning roadmaps.

---

## 🏗️ System Architecture

```
[Resume / CV]      [Job Description]
       │                  │
       ▼                  ▼
[In-Memory Ingestion (PyMuPDF / python-docx)]
       │
       ▼
[Skill Extraction & Normalization (Taxonomy + RapidFuzz)]
       │
       ▼
[Explainable 4-Factor Matching Engine]
 - Required Skill Coverage (60%)
 - Preferred Skill Coverage (10%)
 - Semantic Domain Overlap (20%)
 - Evidence & Experience Depth (10%)
       │
       ▼
[Skill Gap & Priority Ordering (Prerequisite DAG)]
       │
   ┌───┴────────────────────────┐
   ▼                            ▼
[Candidate Compass]      [Recruiter Screener]
- Match Score & Grade    - Bulk Multi-Resume Ranking
- Prioritized Gaps       - Objective Reason Codes
- Curated Course Links   - Candidate Leaderboard
- Adjacent Role Bridges  - Zero-PII Compliance
```

---

## 📂 Repository Structure

```
Bharat 2.0/
├── backend/                  # Python FastAPI service
│   ├── app/
│   │   ├── main.py           # FastAPI entrypoint, safe CORS, health endpoints
│   │   ├── config.py         # Pydantic Settings configuration
│   │   ├── api/v1/           # API v1 routes & health router
│   │   ├── core/             # AI/NLP engines (Taxonomy, Normalizer, Matching, DAG)
│   │   └── utils/            # Document extractors (PDF, DOCX, TXT)
│   ├── tests/                # Pytest unit & regression tests
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile            # Production Python container
├── frontend/                 # Next.js 14+ App Router & TypeScript
│   ├── src/
│   │   ├── app/              # Routes: /, /candidate, /candidate/upload, /candidate/results, /recruiter, /insights
│   │   ├── components/       # Reusable UI (MatchScore, SkillBadge, SkillGapCard, etc.)
│   │   ├── mock/             # Isolated visual mock dataset
│   │   └── lib/              # API client and TypeScript definitions
│   ├── Dockerfile            # Multi-stage production container
│   └── package.json
├── docs/
│   ├── IMPLEMENTATION_PLAN.md # Architectural masterplan
│   └── FOUNDATION_WALKTHROUGH.md # Verification walkthrough report
├── .github/workflows/ci.yml  # GitHub Actions automated test & build pipeline
├── docker-compose.yml        # Multi-container orchestration
└── .env.example              # Environment variables template
```

---

## 🚀 Quickstart Guide

### Prerequisites
- **Node.js**: v20+
- **Python**: 3.9+
- **Docker** (optional for containerized execution)

### 1. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run development server (Port 8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Test endpoints:
- `http://localhost:8000/health`
- `http://localhost:8000/api/v1/health`
- `http://localhost:8000/docs` (Swagger UI)

### 2. Frontend Setup
```bash
cd frontend
npm install

# Run development server (Port 3000)
npm run dev
```

Visit: `http://localhost:3000`

---

## 🧪 Testing

### Backend Tests (Pytest)
```bash
cd backend
./venv/bin/pytest -v
```

### Frontend Tests & Type Checking
```bash
cd frontend
npm test
npm run build
```

## 🚢 Production Deployment

Complete operational guide available at [`docs/PRODUCTION.md`](docs/PRODUCTION.md).

### 1. Configure Environment
```bash
cp .env.example .env.production
# Edit .env.production with strong SECRET_KEY, explicit CORS_ORIGINS, and production DATABASE_URL
```

### 2. Multi-Container Orchestration (Docker)
```bash
docker compose -f docker-compose.production.yml up -d --build
```

### 3. Local / Standalone Production Execution
```bash
# Backend: Run migrations, seed canonical ontology, and launch uvicorn workers
cd backend
python3 scripts/migrate.py
python3 scripts/seed_production.py
./scripts/start_production.sh

# Frontend: Build optimized Next.js bundle and start production server
cd frontend
npm run build
./scripts/start_production.sh
```

---

## 🔒 Security & Privacy
- **Zero-PII Storage**: Candidate contact details are not retained in public demo modes.
- **Pure In-Memory Stream Processing**: Files are parsed in-memory with strict 10MB limits without disk execution.
- **Strict Production Safeguards**: Wildcard CORS rejected; production `SECRET_KEY` validated with minimum 32 characters; debug mode disabled.

