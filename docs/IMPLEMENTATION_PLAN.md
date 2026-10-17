# Career Intelligence: System Architecture & Implementation Plan
**SIH 2026 — CODE YUDH Hackathon**
**Team Move-On Coders**

---

## 1. Executive Summary & Repository Audit

### 1.1 Project Purpose & Core Value Proposition
**Career Intelligence** is an explainable AI talent–job matching and workforce ecosystem built for India. Addressing the acute talent-job disconnect highlighted by NITI Aayog (where millions of graduates apply for limited openings while industries face acute skill shortages), Career Intelligence replaces black-box keyword filtering with transparent, mathematically defensible matching, prerequisite-aware gap analysis, and actionable learning roadmaps.

```
+---------------------------------------------------------------------------------------------------+
|                                      CORE PRODUCT PIPELINE                                        |
|                                                                                                   |
|  [Resume / CV]      [Job Description]                                                             |
|         │                  │                                                                      |
|         ▼                  ▼                                                                      |
|  [Doc Ingestion]    [JD Extraction]                                                               |
|         │                  │                                                                      |
|         ▼                  ▼                                                                      |
|  [Skill Extraction] ──▶ [Skill Normalization] (Canonical Taxonomy + RapidFuzz)                     |
|                                    │                                                              |
|                                    ▼                                                              |
|                    [Explainable Matching Engine]                                                  |
|                     - Required Skill Coverage (60%)                                               |
|                     - Preferred Skill Coverage (10%)                                              |
|                     - Semantic Taxonomy Overlap (20%)                                             |
|                     - Experience & Evidence Depth (10%)                                           |
|                                    │                                                              |
|                                    ▼                                                              |
|                    [Skill Gap & Priority Analyzer]                                                |
|                     (Prerequisite DAG + Unblocking Analysis)                                      |
|                                    │                                                              |
|             ┌──────────────────────┴──────────────────────┐                                       |
|             ▼                                             ▼                                       |
|  [Candidate Workflow]                            [Recruiter Workflow]                             |
|  - Matched vs. Missing breakdown                 - Multi-candidate bulk ranking                   |
|  - Score grade & explainability evidence         - Explainable ranking criteria                   |
|  - Actionable learning roadmap (curated)         - Comparative skill matrix                       |
|  - Adjacent career paths                         - Candidate shortlisting & export                |
+---------------------------------------------------------------------------------------------------+
```

---

### 1.2 Current Repository Inventory
The active workspace (`Bharat 2.0`) currently contains a Python backend core module structure:

```
Bharat 2.0/
├── backend/
│   ├── app/
│   │   ├── __init__.py                # Package version definition (1.0.0)
│   │   ├── core/
│   │   │   ├── taxonomy.py            # Canonical skills catalog (9 categories, 45+ skills, alias map)
│   │   │   ├── normalizer.py          # Multi-stage skill normalizer (exact, punctuation, RapidFuzz)
│   │   │   ├── extractor.py           # Multi-pattern regex extractor with sentence evidence capture
│   │   │   ├── role_engine.py         # 7 curated career roles + dynamic JD parser
│   │   │   ├── matching_engine.py     # Deterministic explainable 4-factor scoring engine
│   │   │   ├── gap_analyzer.py        # Prerequisite-aware gap analyzer & priority scorer
│   │   │   └── roadmap_generator.py   # Milestone planner, curated courses & adjacent role recommender
│   │   └── utils/
│   │       ├── file_extractor.py      # PyMuPDF (PDF) & python-docx (DOCX) text extractor
│   │       └── text_cleaner.py        # Unicode sanitizer & sentence/bullet segmenter
│   ├── requirements.txt               # Backend dependencies (FastAPI, PyMuPDF, python-docx, RapidFuzz, etc.)
│   └── venv/                          # Python 3.9 virtual environment with installed packages
└── docs/                              # Project documentation
```

Reference materials identified in parent and system directories:
- `pitch.pdf` & `Move-On coders.pptx`: Official SIH 2026 CODE YUDH pitch decks outlining project goals, personas, KPIs, architecture, and team structure.
- Legacy parent prototype (`../index.html`, `../script.js`, `../style.css`): Early monolithic HTML/JS mockup.

---

### 1.3 Audit Findings: What Works vs. What is Missing

#### ✅ What Already Works (Verified in Audit):
1. **Document Ingestion (`file_extractor.py`)**: Safe parsing of PDF (PyMuPDF stream) and DOCX (python-docx stream) up to 10MB, with fallback Unicode cleaning and validation.
2. **Text Normalization (`text_cleaner.py`)**: Bullet normalization, whitespace cleaning, and sentence boundary extraction preserving linguistic integrity.
3. **Canonical Skill Taxonomy (`taxonomy.py`)**: Structured ontology covering 9 critical IT/AI domains, alias mapping, prerequisite graphs, and adjacent skill links.
4. **Skill Normalization (`normalizer.py`)**: Exact, punctuation-insensitive, and RapidFuzz token matching (>88% cutoff) preventing short-token hallucinations.
5. **Skill Extraction (`extractor.py`)**: Boundary-safe regex matching that extracts canonical skills, counts frequencies, calculates confidence, and extracts sentence-level evidence snippets.
6. **Explainable Matching (`matching_engine.py`)**: Transparent weighted scoring model (Required 60%, Preferred 10%, Semantic 20%, Depth 10%) producing full factor breakdowns and natural language narratives.
7. **Role Intelligence & JD Parser (`role_engine.py`)**: Predefined benchmark roles (Data Scientist, ML Engineer, Data Analyst, Fullstack, Backend, Cloud/DevOps, Cybersecurity) and automatic JD-to-role translation.
8. **Gap Prioritization (`gap_analyzer.py`)**: Dependency graph analysis ordering missing skills by prerequisites met, unblocking power, and role criticality.
9. **Roadmap & Adjacent Roles (`roadmap_generator.py`)**: Curated verified course links (Coursera, MIT OCW, freeCodeCamp, official docs), project challenges, and adjacent lateral role discovery.

#### ❌ What is Missing / Incomplete:
1. **FastAPI Application & HTTP Routing**: No `main.py`, API routes, request/response validation schemas, CORS middleware, or file upload endpoints.
2. **Persistence / Database Layer**: No database schema, SQLAlchemy models, migration files, or session management for persisting candidate analyses, uploaded resumes, or recruiter job campaigns.
3. **Modern Frontend Application**: No Next.js project initialized in the workspace. An enterprise-grade, modern dashboard (Next.js + TypeScript + Tailwind CSS + shadcn/ui) is required.
4. **NLP / Embedding Augmentation**: While deterministic regex and RapidFuzz are operational, semantic similarity between unstructured JD statements and candidate profiles can be enhanced using lightweight sentence embeddings (`sentence-transformers/all-MiniLM-L6-v2`) or spaCy entity matching.
5. **Automated Test Suite**: No Pytest test suite in `backend/tests/` and no Playwright E2E browser tests.
6. **Containerization & Deployment**: No `Dockerfile`, `docker-compose.yml`, or production environment configuration.

---

## 2. Target System Architecture

```
                                  USER BROWSER / CLIENT
                                            │
                    ┌───────────────────────┴───────────────────────┐
                    ▼                                               ▼
         [Candidate Portal (Next.js)]                   [Recruiter Portal (Next.js)]
         - Resume Upload & Drag-and-drop                - Bulk Multi-Resume Ingestion
         - Live Skill Extraction Badge Preview          - Job Description Editor & Parser
         - Role Selection & JD Match Trigger            - Ranked Talent Table & Score Radar
         - Explainable Factor Breakdown Cards           - Gap Comparison Matrix
         - Milestone Roadmap & Resource Links           - Candidate CSV/JSON Export
                    │                                               │
                    └───────────────────────┬───────────────────────┘
                                            │ HTTPS / REST JSON
                                            ▼
                               [FastAPI Gateway (Port 8000)]
         - CORS Middleware, Request Validation, Error Handling, Rate Limiting
                                            │
               ┌────────────────────────────┼────────────────────────────┐
               ▼                            ▼                            ▼
      [Document Service]           [Core AI / NLP Engine]       [Storage & Persistence]
      - PyMuPDF Parser             - Taxonomy & Alias Matcher   - PostgreSQL 16 (Relational)
      - python-docx Parser         - RapidFuzz Normalizer       - SQLAlchemy 2.0 Async/Sync
      - Text Sanitizer & Evidence  - Weighted Match Scorer      - Local / S3 File Storage
                                   - Prerequisite Gap Engine    - Structured Audit Logs
                                   - Roadmap & Course Generator
```

---

## 3. Directory & Folder Structure

```
Bharat 2.0/
├── docs/
│   └── IMPLEMENTATION_PLAN.md         # This architectural masterplan
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI application entrypoint & middleware
│   │   ├── config.py                  # Pydantic Settings (env variables, DB URLs, thresholds)
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py                # Database and engine dependencies
│   │   │   ├── candidate.py           # Candidate workflow endpoints (parse, match, roadmap)
│   │   │   ├── recruiter.py           # Recruiter workflow endpoints (parse-jd, rank-bulk)
│   │   │   ├── roles.py               # Predefined roles & taxonomy query endpoints
│   │   │   └── analytics.py           # Workforce analytics and skill demand endpoints
│   │   ├── core/                      # (Existing audited engines)
│   │   │   ├── taxonomy.py
│   │   │   ├── normalizer.py
│   │   │   ├── extractor.py
│   │   │   ├── role_engine.py
│   │   │   ├── matching_engine.py
│   │   │   ├── gap_analyzer.py
│   │   │   └── roadmap_generator.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── session.py             # SQLAlchemy engine & sessionmaker
│   │   │   ├── base.py                # Declarative Base
│   │   │   └── models.py              # User, Resume, Job, MatchAnalysis, Roadmap models
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── candidate.py           # Pydantic schemas for candidate requests/responses
│   │   │   ├── recruiter.py           # Pydantic schemas for recruiter ranking
│   │   │   └── common.py              # Shared schemas (skills, errors, metadata)
│   │   └── utils/
│   │       ├── file_extractor.py
│   │       └── text_cleaner.py
│   ├── tests/
│   │   ├── conftest.py                # Test fixtures, mock files, DB session
│   │   ├── test_file_extractor.py     # Document extraction tests
│   │   ├── test_extractor.py          # Skill extraction & evidence tests
│   │   ├── test_normalizer.py         # Normalizer & RapidFuzz tests
│   │   ├── test_matching.py           # Deterministic 4-factor scoring tests
│   │   ├── test_gap_analyzer.py       # Prerequisite DAG & priority ranking tests
│   │   ├── test_roadmap.py            # Roadmap & adjacent roles tests
│   │   └── test_api_endpoints.py      # FastAPI HTTP integration tests
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/                          # Next.js 14+ App Router Application
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx             # Root layout with navbar, theme, and font providers
│   │   │   ├── page.tsx               # Landing page showcasing the dual workflows & demo
│   │   │   ├── candidate/
│   │   │   │   ├── page.tsx           # Candidate interactive evaluation wizard
│   │   │   │   └── results/
│   │   │   │       └── page.tsx       # Explainable results, gap radar, roadmap timeline
│   │   │   ├── recruiter/
│   │   │   │   ├── page.tsx           # Recruiter JD parser & bulk candidate upload
│   │   │   │   └── results/
│   │   │   │       └── page.tsx       # Ranked candidate leaderboard & comparative matrix
│   │   │   ├── roles/
│   │   │   │   └── page.tsx           # Career role catalog & market demand overview
│   │   │   └── analytics/
│   │   │       └── page.tsx           # Workforce intelligence & skill shortage dashboard
│   │   ├── components/
│   │   │   ├── ui/                    # Accessible UI components (Button, Card, Badge, Dialog, etc.)
│   │   │   ├── candidate/
│   │   │   │   ├── ResumeUploader.tsx # Drag-and-drop resume upload with file preview
│   │   │   │   ├── SkillTagCloud.tsx  # Interactive categorized skill badges with evidence popover
│   │   │   │   ├── MatchGauge.tsx     # Animated SVG radial score gauge
│   │   │   │   ├── FactorBreakdown.tsx# Explainable 4-factor progress bars
│   │   │   │   ├── GapMatrix.tsx      # Matched vs. Missing vs. Partial comparison
│   │   │   │   ├── RoadmapTimeline.tsx# Milestone sequence with course links & project cards
│   │   │   │   └── AdjacentRoles.tsx  # Lateral pivot opportunity cards
│   │   │   ├── recruiter/
│   │   │   │   ├── JDEditor.tsx       # Textarea + sample JD templates + skill auto-tagger
│   │   │   │   ├── BulkUploader.tsx   # Multi-file batch uploader with status badges
│   │   │   │   ├── CandidateRankTable.tsx # Sortable leaderboard with scores, gaps, and exports
│   │   │   │   └── CandidateDetailModal.tsx # Full explainability view for any selected applicant
│   │   │   └── layout/
│   │   │       ├── Navbar.tsx         # Responsive navigation header
│   │   │       └── Footer.tsx
│   │   ├── lib/
│   │   │   ├── api.ts                 # Typed fetch client connecting to FastAPI backend
│   │   │   ├── types.ts               # Shared TypeScript interfaces
│   │   │   └── utils.ts               # Tailwind class merger and formatting helpers
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── Dockerfile
├── docker-compose.yml                 # Multi-container orchestration (FastAPI + Next.js + PostgreSQL)
└── README.md
```

---

## 4. Database Schema Design (PostgreSQL)

```sql
-- =========================================================================
-- CAREER INTELLIGENCE RELATIONAL SCHEMA
-- =========================================================================

-- 1. Resumes / Profiles
CREATE TABLE resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_name VARCHAR(255) NULL,
    candidate_email VARCHAR(255) NULL,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    raw_text TEXT NOT NULL,
    sanitized_text TEXT NOT NULL,
    extracted_skills_json JSONB NOT NULL,
    total_skills_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Job Descriptions / Roles
CREATE TABLE job_descriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    role_category VARCHAR(100) NOT NULL,
    company_name VARCHAR(255) NULL,
    source_type VARCHAR(50) NOT NULL DEFAULT 'custom_jd', -- 'predefined_role' or 'custom_jd'
    raw_text TEXT NOT NULL,
    parsed_skills_json JSONB NOT NULL,
    typical_experience_years INT DEFAULT 2,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Match Evaluations (Candidate & Recruiter Runs)
CREATE TABLE match_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID REFERENCES resumes(id) ON DELETE CASCADE,
    job_id UUID REFERENCES job_descriptions(id) ON DELETE CASCADE,
    target_role_title VARCHAR(255) NOT NULL,
    overall_match_score NUMERIC(5, 2) NOT NULL,
    score_grade VARCHAR(50) NOT NULL,
    factor_breakdown_json JSONB NOT NULL,
    matched_skills_json JSONB NOT NULL,
    partial_skills_json JSONB NOT NULL,
    missing_skills_json JSONB NOT NULL,
    explainability_narrative TEXT NOT NULL,
    weights_used_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Learning Roadmaps
CREATE TABLE learning_roadmaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID REFERENCES match_evaluations(id) ON DELETE CASCADE,
    target_role VARCHAR(255) NOT NULL,
    total_estimated_weeks INT NOT NULL,
    total_milestones INT NOT NULL,
    milestones_json JSONB NOT NULL,
    adjacent_roles_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Canonical Skills Catalog (Dynamic Sync with taxonomy.py)
CREATE TABLE skills_catalog (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    aliases_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    description TEXT,
    prerequisites_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    adjacent_skills_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    importance_weight NUMERIC(3, 2) DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indices for performance
CREATE INDEX idx_evaluations_resume ON match_evaluations(resume_id);
CREATE INDEX idx_evaluations_job ON match_evaluations(job_id);
CREATE INDEX idx_evaluations_score ON match_evaluations(overall_match_score DESC);
CREATE INDEX idx_skills_category ON skills_catalog(category);
```

---

## 5. API Specification Design (FastAPI)

All endpoints return standard JSON responses and error envelopes with descriptive HTTP status codes.

### 5.1 Common & Health Endpoints
- `GET /api/health`
  - Response: `{"status": "ok", "version": "1.0.0", "timestamp": "2026-09-27T12:00:00Z"}`
- `GET /api/roles`
  - Returns list of 7 benchmark career roles with required/preferred skills.
- `GET /api/taxonomy/skills`
  - Returns all canonical skills grouped by 9 domains.

### 5.2 Candidate Workflow Endpoints
- `POST /api/candidate/parse-resume`
  - **Input**: `multipart/form-data` with `file: UploadFile` (PDF/DOCX/TXT).
  - **Output**:
    ```json
    {
      "resume_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "filename": "candidate_resume.pdf",
      "character_count": 3410,
      "total_skills_detected": 14,
      "categories_found": ["Programming", "Data Science & AI", "Databases & Storage"],
      "skills": [
        {
          "canonical_id": "python",
          "canonical_name": "Python",
          "category": "Programming",
          "confidence": 0.99,
          "frequency": 4,
          "evidence": [
            "Developed automated data pipelines using Python and SQL.",
            "Built predictive ML models with Python scikit-learn."
          ]
        }
      ]
    }
    ```

- `POST /api/candidate/analyze`
  - **Input**:
    ```json
    {
      "resume_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "target_role_id": "data_scientist",
      "custom_jd_text": null,
      "custom_weights": null
    }
    ```
  - **Output**:
    ```json
    {
      "evaluation_id": "c3a2f1b4-...",
      "target_role_title": "Data Scientist",
      "overall_match_score": 78.5,
      "score_grade": "High Alignment",
      "factor_breakdown": [
        {
          "factor_name": "Required Skill Coverage",
          "raw_score": 83.3,
          "weight": 0.60,
          "weighted_score": 50.0,
          "max_possible_points": 60.0,
          "explanation": "Matched 5 of 6 required core skills directly, with 1 partial competency."
        }
      ],
      "matched_required": [...],
      "partial_skills": [...],
      "missing_required": [...],
      "explainability_narrative": "Overall match score of 78.5% for Data Scientist...",
      "gap_report": {
        "readiness_percentage": 83.3,
        "prioritized_gaps": [
          {
            "skill_id": "statistics_probability",
            "canonical_name": "Statistics & Probability",
            "priority_tier": "P1 - Foundational (Learn First)",
            "priority_score": 12.5,
            "prerequisites_met": true,
            "unblocks_skills": ["Machine Learning"],
            "learning_effort_weeks": "2-3 weeks",
            "reasoning": "Crucial core requirement... Unblocks subsequent learning..."
          }
        ]
      },
      "roadmap": {
        "total_estimated_weeks": 8,
        "total_milestones": 3,
        "milestones": [...]
      },
      "adjacent_roles": [
        {
          "role_id": "ml_engineer",
          "role_title": "Machine Learning Engineer",
          "alignment_score": 74.2,
          "transition_feasibility": "Moderate Bridge Required"
        }
      ]
    }
    ```

### 5.3 Recruiter Workflow Endpoints
- `POST /api/recruiter/parse-jd`
  - **Input**: `{ "title": "Senior Backend Developer", "jd_text": "We are seeking a Python developer with FastAPI, PostgreSQL, Docker..." }`
  - **Output**: Canonical role profile with auto-tagged required & preferred skills.

- `POST /api/recruiter/rank-candidates`
  - **Input**: `multipart/form-data` with:
    - `files: List[UploadFile]` (Batch of 2 to 50 resumes)
    - `target_role_id: Optional[str]`
    - `jd_text: Optional[str]`
    - `jd_title: Optional[str]`
  - **Output**:
    ```json
    {
      "job_title": "Senior Backend Developer",
      "total_candidates_processed": 5,
      "ranked_candidates": [
        {
          "rank": 1,
          "candidate_name": "Pawan Kumar",
          "filename": "pawan_resume.pdf",
          "overall_match_score": 88.5,
          "score_grade": "Exceptional Match",
          "required_coverage_pct": 92.0,
          "matched_skills_count": 8,
          "missing_required_skills": ["Kubernetes (K8s)"],
          "top_strengths": ["FastAPI", "Python", "PostgreSQL", "Docker"],
          "explainability_summary": "Top applicant with direct evidence across all required backend frameworks."
        }
      ]
    }
    ```

### 5.4 Analytics Endpoints
- `GET /api/analytics/in-demand-skills`
  - Returns aggregation of most frequently requested skills across predefined roles and benchmark data.

---

## 6. Frontend Route & Page Structure (Next.js)

| Route | Page Name | Primary Features |
|---|---|---|
| `/` | Landing / Launchpad | Value proposition, interactive architecture diagram, workflow selector (Candidate vs. Recruiter), quick demo launcher. |
| `/candidate` | Candidate Evaluation Wizard | 3-step intuitive wizard: (1) Drag-and-drop resume upload with instant extraction preview, (2) Target role selection or custom JD paste, (3) Instant scoring trigger. |
| `/candidate/results` | Explainable Match & Roadmap | Dynamic animated score gauge, 4-factor breakdown bars, categorized skill gap matrix, prerequisite-ordered learning roadmap with course links, adjacent role cards. |
| `/recruiter` | Recruiter Talent Engine | Dual-input workspace: Job description text area with auto-extraction chips alongside multi-resume batch uploader. |
| `/recruiter/results` | Candidate Leaderboard | Sortable applicant ranking table, score badges, required skill coverage bars, missing skill alerts, full applicant explainability modal, CSV/JSON export. |
| `/roles` | Career Roles Explorer | Grid view of 7 pre-defined benchmark roles with skill breakdown, market demand index, and salary context. |
| `/analytics` | Workforce Intelligence | Macro skill shortage indicators, curriculum-to-market alignment cards, category distribution charts. |

---

## 7. ML & NLP Pipeline Architecture

### 7.1 Text Extraction & Preprocessing
1. **PyMuPDF (`fitz`)**: Fast, in-memory PDF stream decoding capable of multi-column text extraction without temporary disk writes.
2. **`python-docx`**: Structural paragraph and table traversal, preserving tabular skill listings commonly found in technical resumes.
3. **`text_cleaner.py`**: Unicode normalization (non-breaking spaces, em-dashes, smart quotes, bullet marks) and linguistic sentence splitting using regex lookbehinds (`(?<=[.!?])\s+(?=[A-Z0-9])`).

### 7.2 Hybrid Skill Extraction
```
Input Text ──▶ Sentence Segmentation ──▶ Compiled Boundary Regex Matcher ──▶ Canonical ID Lookup
                                                         │
                                                         ▼
                                            Confidence & Frequency Scorer
                                                         │
                                                         ▼
                                          Sentence Evidence Snippet Store
```
- **Boundary Precision**: Uses negative lookbehind `(?<![a-zA-Z0-9_])` and lookahead `(?![a-zA-Z0-9_])` to cleanly extract tokens like `C++`, `C#`, `.NET`, `Go`, `R`, avoiding false substrings (e.g., matching "go" inside "algorithm").
- **Evidence Extraction**: Automatically attaches up to 3 sentence citations per detected skill (e.g., `"Implemented PyTorch neural networks for image classification"` for `pytorch`).

### 7.3 Canonical Normalization & RapidFuzz Fallback
- **Exact & Alias Index**: O(1) hash map lookup across 300+ aliases and variants.
- **Punctuation Normalizer**: Maps `node.js` -> `nodejs` -> `node_js`.
- **Fuzzy Token Matching**: RapidFuzz ratio scorer with an 88% cutoff applied strictly to tokens >= 3 characters to resolve typos without false positives.

### 7.4 Explainable Scoring Formula
$$\text{Score} = w_{req} \cdot S_{req} + w_{pref} \cdot S_{pref} + w_{sem} \cdot S_{sem} + w_{exp} \cdot S_{exp}$$
Where:
- $w_{req} = 0.60$ (Required Skill Coverage, with 100% for direct match and 45% partial credit for adjacent skills).
- $w_{pref} = 0.10$ (Preferred / Nice-to-Have Coverage).
- $w_{sem} = 0.20$ (Taxonomy Domain Overlap between candidate categories and target role categories).
- $w_{exp} = 0.10$ (Evidence Depth: ratio of verified skills and citation sentences).

### 7.5 Prerequisite DAG & Gap Prioritization
- Evaluates missing skills against a directed prerequisite graph.
- Missing skills whose prerequisites are already satisfied receive highest priority ($P1$), unblocking subsequent learning milestones.

---

## 8. Security, Privacy & Performance

1. **Zero-PII Storage Policy**: In public hackathon demo mode, candidate contact details (phone, email, address) are sanitized or excluded from long-term database storage.
2. **File Upload Hardening**:
   - Strict 10MB file limit enforcement before reading into memory.
   - Extension and MIME-type gating (`.pdf`, `.docx`, `.txt`).
   - Pure stream parsing with no execution of embedded macros or external commands.
3. **CORS & Rate Limiting**:
   - FastAPI CORS restricted to the frontend origin in production.
   - Throttling on bulk recruiter upload endpoints to prevent memory exhaustion.
4. **Performance Target (Hackathon KPI)**:
   - Complete end-to-end resume parse, match calculation, and roadmap generation in **< 1.5 seconds**.

---

## 9. Testing Strategy

### 9.1 Unit & Integration Testing (Pytest)
- `tests/test_file_extractor.py`: Test clean and malformed PDF/DOCX streams; verify file size limits and unsupported extensions.
- `tests/test_extractor.py`: Test boundary regex for difficult tokens (`C++`, `Go`, `SQL`, `React.js`); verify sentence evidence extraction.
- `tests/test_normalizer.py`: Test alias mapping (`py` -> `python`, `k8s` -> `kubernetes`) and fuzzy cutoff thresholds.
- `tests/test_matching.py`: Validate the 4-factor scoring formula against mathematical ground truth; test partial match weights.
- `tests/test_gap_analyzer.py`: Verify DAG dependency ordering (ensuring Python/Math precedes Deep Learning).
- `tests/test_api_endpoints.py`: Test FastAPI `/api/candidate/parse-resume`, `/api/candidate/analyze`, and `/api/recruiter/rank-candidates`.

### 9.2 End-to-End Testing (Playwright)
- Test full Candidate journey: Upload sample resume -> Select Data Scientist -> Verify match score gauge -> View roadmap.
- Test full Recruiter journey: Paste JD -> Upload 3 resumes -> Verify ranked order table and candidate comparison modal.

---

## 10. Deployment Architecture

### 10.1 Docker Multi-Container Compose
```yaml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    container_name: career_intel_db
    restart: always
    environment:
      POSTGRES_DB: career_intelligence
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: career_intel_api
    restart: always
    environment:
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD:-postgres}@db:5432/career_intelligence
      CORS_ORIGINS: "http://localhost:3000"
    ports:
      - "8000:8000"
    depends_on:
      - db

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: career_intel_web
    restart: always
    environment:
      NEXT_PUBLIC_API_URL: "http://localhost:8000"
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  pgdata:
```

---

## 11. Prioritized Implementation Phases

| Phase | Objective | Scope & Key Deliverables |
|---|---|---|
| **Phase 1** | Backend API & Persistence | Create `main.py`, FastAPI routers (`candidate.py`, `recruiter.py`, `roles.py`), SQLAlchemy models, and SQLite/PostgreSQL database integration. |
| **Phase 2** | Backend Unit & Integration Tests | Write full Pytest test suite in `backend/tests/` covering file extraction, normalizer, matching engine, and API routes. |
| **Phase 3** | Frontend Foundation (Next.js) | Initialize Next.js with TypeScript, Tailwind CSS, Lucide icons, and modern design system tokens (dark mode, glassmorphism, responsive navigation). |
| **Phase 4** | Candidate Workflow UI | Build `ResumeUploader`, interactive skill tags, animated match score gauge, 4-factor breakdown bars, gap matrix, and milestone roadmap. |
| **Phase 5** | Recruiter Workflow UI | Build JD editor with auto-tagging, batch resume uploader, ranked candidate leaderboard, and applicant comparison modal. |
| **Phase 6** | E2E Testing, Dockerization & Polish | Docker multi-stage builds, `docker-compose.yml`, Playwright E2E tests, and hackathon presentation demo script validation. |

---

## 12. Acceptance Criteria & Demo Script Alignment

To satisfy SIH 2026 hackathon judging criteria:
1. **Explainability**: Every score displayed must show the exact math (60% required + 10% preferred + 20% semantic + 10% depth) and direct sentence evidence citations from the candidate's resume.
2. **Speed KPI**: Candidate single evaluation runs in under 1.5 seconds; recruiter batch of 5 resumes ranks in under 4 seconds.
3. **No Hallucinated Courses**: All recommended learning resources must point to reputable providers (Coursera, MIT OCW, freeCodeCamp, official docs).
4. **Resilience**: Clean handling of corrupted files, scanned non-OCR PDFs, empty text inputs, and edge-case job titles.
