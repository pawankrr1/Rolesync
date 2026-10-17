# Foundation Walkthrough: Career Intelligence

> **SIH 2026 — Build for Bharat 2.0 Hackathon**  
> **Team: Move-On Coders**  
> **Tagline:** MATCH → GAP → LEARN → GROW

---

## 1. Overview of Work Completed

In accordance with the foundational milestones specified in `docs/IMPLEMENTATION_PLAN.md`, we established the complete repository monorepo structure, FastAPI backend service, Next.js 14+ App Router frontend, design system, component library, test suites, and container configurations without implementing fake or prematurely mocked business logic.

---

## 2. Inventory of Created Files & Modules

### 2.1 Backend Layer (`backend/`)
- `app/main.py`: Production-grade FastAPI entrypoint with safe CORS middleware (`CORSMiddleware`), root endpoint (`GET /`), and root health check (`GET /health`).
- `app/config.py`: Pydantic `BaseSettings` managing server host/port, environment flags, CORS origins parsing, and database connection strings.
- `app/api/v1/router.py`: API v1 master router aggregating versioned endpoint routers.
- `app/api/v1/endpoints/health.py`: Versioned health endpoint (`GET /api/v1/health`) returning service status, project name, version, and environment.
- `pytest.ini`: Configured test runner with `-v --tb=short` and automatic test discovery in `tests/`.
- `tests/conftest.py`: Shared pytest fixture providing FastAPI `TestClient(app)`.
- `tests/test_health.py`: Unit tests validating `GET /`, `GET /health`, `GET /api/v1/health`, and CORS headers.
- `tests/test_existing_modules.py`: Regression verification suite asserting existing core modules (`taxonomy.py`, `normalizer.py`, `extractor.py`, `role_engine.py`, `matching_engine.py`, `gap_analyzer.py`, `roadmap_generator.py`, `text_cleaner.py`) remain 100% operational.
- `Dockerfile`: Multi-stage Python 3.9-slim container configuration with healthcheck instructions.
- `.dockerignore`: Excludes cache, virtual environments, and local files.
- `.env.example`: Backend environment variable template.

### 2.2 Frontend Layer (`frontend/`)
- `package.json`: Configured with Next.js 16 (App Router), React 19, TypeScript 5, Tailwind CSS 4, `lucide-react`, `clsx`, `tailwind-merge`, and custom test runner script (`npm test`).
- `src/lib/types.ts`: Comprehensive domain interfaces (`SkillItem`, `FactorBreakdownItem`, `SkillGapItem`, `RoadmapMilestoneItem`, `AdjacentRoleItem`, `CandidateAnalysisSummary`, `RecruiterApplicantItem`, `MarketInsightMetric`).
- `src/mock/careerMockData.ts`: **Strictly isolated visual mock dataset** for UI development (`mockWorkflowSteps`, `mockCandidateProfile`, `mockAnalysisResult`, `mockRecruiterApplicants`, `mockMarketInsights`).
- `src/lib/api.ts`: Typed fetch client for backend communication with latency tracking and health checking (`checkBackendHealth()`).

#### Reusable UI Components (`src/components/ui/`):
- `MatchScore.tsx`: Animated SVG radial circular score gauge with dynamic color themes (Emerald, Blue, Amber, Rose) and grade badges.
- `SkillBadge.tsx`: Categorized skill badge with confidence percentage, status icons (Matched, Partial, Missing), and interactive evidence popover tooltip.
- `SkillGroup.tsx`: Categorized container grouping skills by technical domain with count pill.
- `SkillGapCard.tsx`: Prioritized missing skill card featuring priority rank (#1, #2), tier badge (P1, P2, P3), unblocked skills, prerequisite met status, and estimated study duration.
- `RecommendationCard.tsx`: Curated course and milestone card with provider badge (MIT OCW, Coursera, freeCodeCamp), estimated hours, hands-on capstone challenge, and outcomes.
- `RoleMatchCard.tsx`: Adjacent career mobility card showing alignment percentage, overlapping skills, bridge skills, and transition feasibility.
- `UploadZone.tsx`: Drag-and-drop file upload zone accepting `.pdf`, `.docx`, and `.txt` up to 10MB, with format validation and quick demo sample buttons.
- `ProgressIndicator.tsx`: Interactive horizontal pipeline tracker illustrating the 6-step workflow (*Ingest → Extract → Normalize → Match → Gap → Recommend*).
- `ExplanationPanel.tsx`: Transparent 4-factor score breakdown card (Required 60%, Preferred 10%, Semantic 20%, Depth 10%) with progress bars and natural language engine summary.

#### Layout & Common States (`src/components/layout/` & `src/components/common/`):
- `Navbar.tsx`: Global navigation header with branding, live API status indicator dot (querying `/api/v1/health`), and quick CTAs.
- `Footer.tsx`: SIH 2026 Build for Bharat 2.0 attribution, Team Move-On Coders roster, and Zero-PII privacy guarantee.
- `DashboardSidebar.tsx`: Persistent contextual workspace navigation for Candidate and Recruiter sections.
- `LoadingState.tsx`: Animated circular pulse and stage spinner for pipeline processing states.
- `EmptyState.tsx`: Clean empty state illustration with action button for unpopulated lists.
- `ErrorState.tsx`: Friendly alert card with error diagnosis and retry trigger.

#### Page Shells (`src/app/`):
- `/`: **Landing Page** featuring the hero headline ("Know where you stand. Know what to learn next."), supporting text, primary CTA ("Analyze My Career"), secondary CTA ("I'm a Recruiter"), 6-step workflow cards, dual workflow boxes, and interactive score preview.
- `/candidate`: **Candidate Dashboard Shell** displaying candidate profile header, benchmark role alignment highlight, verified extracted skills badge cloud, and quick transition opportunities.
- `/candidate/upload`: **Resume Upload Shell** with `UploadZone`, step progress indicator, target role selector (Predefined Benchmark Roles vs. Custom JD paste), and live skill extraction preview.
- `/candidate/results`: **Analysis Results Shell** integrating `MatchScore`, `ExplanationPanel`, 3-column `SkillGroup` breakdown, `SkillGapCard` prioritized DAG list, `RecommendationCard` course milestones, and `RoleMatchCard` adjacent paths.
- `/recruiter`: **Recruiter Dashboard Shell** featuring dual job description editor and bulk resume ingestion zone, sortable candidate leaderboard table, and full applicant detail inspection modal.
- `/insights`: **Market Insights Shell** displaying NITI Aayog 340:1 disconnect metrics, top in-demand tech skills, and curriculum vs. industry readiness disconnect table.

### 2.3 Root Infrastructure & Orchestration
- `.gitignore`: Comprehensive ignore rules for Node.js, Python, virtual environments, build outputs, and `.env` secret files.
- `.env.example`: Root environment variables template.
- `docker-compose.yml`: Multi-service development and production orchestration definition (`career_intel_backend` on port 8000 and `career_intel_frontend` on port 3000).
- `.github/workflows/ci.yml`: Automated GitHub Actions pipeline executing backend Pytest and frontend build/type checking on all branches.
- `README.md`: Professional project documentation including problem statement, architecture diagram, monorepo directory tree, quickstart guide, and testing instructions.

---

## 3. Verification & Execution Log

### 3.1 Backend Verification
1. **Pytest Test Suite**:
   ```bash
   cd backend
   ./venv/bin/pytest -v
   ```
   **Output:**
   ```
   tests/test_existing_modules.py::test_taxonomy_intact PASSED              [ 11%]
   tests/test_existing_modules.py::test_normalizer_intact PASSED            [ 22%]
   tests/test_existing_modules.py::test_extractor_intact PASSED             [ 33%]
   tests/test_existing_modules.py::test_matching_and_gaps_intact PASSED     [ 44%]
   tests/test_existing_modules.py::test_text_cleaner_intact PASSED          [ 55%]
   tests/test_health.py::test_root_endpoint PASSED                          [ 66%]
   tests/test_health.py::test_root_health_endpoint PASSED                   [ 77%]
   tests/test_health.py::test_api_v1_health_endpoint PASSED                 [ 88%]
   tests/test_health.py::test_cors_headers PASSED                           [100%]
   ============================== 9 passed in 0.09s ===============================
   ```

2. **Live Backend Health Endpoints**:
   - `GET http://127.0.0.1:8000/health`:
     ```json
     {"status":"healthy","service":"Career Intelligence API","version":"1.0.0","environment":"development"}
     ```
   - `GET http://127.0.0.1:8000/api/v1/health`:
     ```json
     {"status":"healthy","service":"Career Intelligence API","version":"1.0.0","environment":"development","api_prefix":"/api/v1"}
     ```

### 3.2 Frontend Verification
1. **Frontend Test Suite & TypeScript Compilation**:
   ```bash
   cd frontend
   npm test
   ```
   **Output:**
   ```
   === RUNNING FRONTEND TEST SUITE ===
   ✓ Route verified: src/app/page.tsx
   ✓ Route verified: src/app/candidate/page.tsx
   ✓ Route verified: src/app/candidate/upload/page.tsx
   ✓ Route verified: src/app/candidate/results/page.tsx
   ✓ Route verified: src/app/recruiter/page.tsx
   ✓ Route verified: src/app/insights/page.tsx
   ✓ All 15 required UI and layout components verified
   Running TypeScript compilation check (tsc --noEmit)...
   ✓ TypeScript check passed with 0 errors!
   ✅ ALL FRONTEND VERIFICATION TESTS PASSED!
   ```

2. **Next.js Production Build**:
   ```bash
   cd frontend
   npm run build
   ```
   **Output:**
   ```
   Route (app)
   ┌ ○ /
   ├ ○ /_not-found
   ├ ○ /candidate
   ├ ○ /candidate/results
   ├ ○ /candidate/upload
   ├ ○ /insights
   └ ○ /recruiter
   ○ (Static) prerendered as static content
   ✓ Compiled successfully with zero TypeScript or bundling errors.
   ```

3. **Live Route Health Checks**:
   - `/`: `HTTP 200 OK`
   - `/candidate`: `HTTP 200 OK`
   - `/candidate/upload`: `HTTP 200 OK`
   - `/candidate/results`: `HTTP 200 OK`
   - `/recruiter`: `HTTP 200 OK`
   - `/insights`: `HTTP 200 OK`

4. **Frontend-to-Backend Health Communication**:
   Verified over HTTP with simulated browser CORS headers:
   ```json
   {
     "status": "healthy",
     "service": "Career Intelligence API",
     "version": "1.0.0",
     "environment": "development",
     "api_prefix": "/api/v1"
   }
   ```

---

## 4. Remaining Work (Next Phases)

Having established a solid, verified foundation, the remaining roadmap aligns directly with the phases defined in `docs/IMPLEMENTATION_PLAN.md`:

1. **Phase 2: Database Persistence & ORM**:
   - Implement SQLAlchemy 2.0 models (`Resume`, `JobDescription`, `MatchEvaluation`, `LearningRoadmap`) and session dependencies in `backend/app/db/`.
   - Setup migration scripts and SQLite/PostgreSQL dynamic engine connection.

2. **Phase 3: Real Candidate API Integration**:
   - Connect `POST /api/candidate/parse-resume` to `app.utils.file_extractor` and `app.core.extractor`.
   - Connect `POST /api/candidate/analyze` to `app.core.matching_engine`, `app.core.gap_analyzer`, and `app.core.roadmap_generator`.
   - Replace visual mock data in frontend upload and results pages with live API mutations.

3. **Phase 4: Real Recruiter Multi-Resume API Integration**:
   - Connect `POST /api/recruiter/parse-jd` and `POST /api/recruiter/rank-candidates`.
   - Implement multipart batch ingestion for parallel resume ranking.

4. **Phase 5: Playwright E2E Tests & Docker Compose Validation**:
   - Write end-to-end browser user journey tests for candidate upload and recruiter ranking.
   - Run complete multi-container stack with `docker-compose up`.
