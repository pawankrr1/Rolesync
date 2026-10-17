"""Comprehensive Performance Profiling Script for Career Intelligence.

Measures:
1. Frontend Initial Load (HTTP latency across routes)
2. Resume Upload (POST /api/v1/documents/parse)
3. Document Parsing (PyMuPDF, python-docx, text parser)
4. Skill Extraction (SkillExtractor 4-layer engine)
5. Matching (Single match & Recruiter batch matching)
6. Dashboard Rendering & API Payload Size (/api/v1/insights/market-intelligence)
"""

import io
import time
import json
import statistics
import urllib.request
import urllib.error
import fitz  # PyMuPDF
import docx
from fastapi.testclient import TestClient

from app.main import app
from app.services.document_parser import parse_document
from app.core.extractor import extractor
from app.core.normalizer import normalizer
from app.core.matching_engine import matching_engine
from app.core.recruiter_engine import recruiter_engine, CandidateInputPayload
from app.services.market_intelligence import get_complete_market_intelligence

SAMPLE_RESUME_TEXT = """
Pawan Kumar
Senior Full Stack Engineer & Cloud Architect
Email: pawan.kumar@example.com | Phone: +91 98765 43210 | Bengaluru, India

PROFESSIONAL SUMMARY
Results-driven software engineer with 5+ years of experience designing, scaling, and maintaining
distributed cloud applications and machine learning pipelines. Expertise in Python, TypeScript,
FastAPI, React.js, Docker, Kubernetes, and PostgreSQL. Proven track record in optimizing backend
systems for high availability and low latency.

TECHNICAL SKILLS
- Programming Languages: Python, TypeScript, JavaScript, SQL, Bash Shell, Go
- Frameworks & Libraries: FastAPI, Django, React.js, Next.js, Node.js, Pandas, Scikit-Learn, PyTorch
- Cloud & DevOps: Amazon Web Services (AWS), Docker, Kubernetes (K8s), CI/CD Pipelines, Linux Systems, Terraform
- Databases: PostgreSQL, Redis, MongoDB, MySQL
- Methodologies: Microservices, REST APIs, System Design, Unit Testing, Agile

PROFESSIONAL EXPERIENCE
Senior Software Engineer | TechCorp India | 2022 - Present
- Architected and deployed microservices backend using FastAPI and Docker on AWS EKS cluster.
- Implemented automated CI/CD pipelines reducing deployment time by 45%.
- Built REST APIs handling 5,000+ requests per second with PostgreSQL indexing and caching.
- Collaborated with data scientists to integrate machine learning inference models using PyTorch and Scikit-Learn.
- Authored automated unit and integration tests achieving 92% code coverage.

Software Engineer | InnovateTech Solutions | 2019 - 2022
- Developed responsive web interfaces using React.js, TypeScript, and TailwindCSS.
- Built backend services in Python and Django with PostgreSQL database queries.
- Automated system provisioning using Terraform and Docker containers.
- Conducted code reviews and mentored junior engineers in clean code and software architecture.

EDUCATION
Bachelor of Technology in Computer Science & Engineering | VTU Karnataka | 2015 - 2019
"""

def generate_pdf_bytes(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((40, 60), text, fontsize=9)
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes

def generate_docx_bytes(text: str) -> bytes:
    doc = docx.Document()
    for line in text.strip().split("\n"):
        if line.strip():
            doc.add_paragraph(line.strip())
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def benchmark_function(fn, iterations=20, warmup=3):
    for _ in range(warmup):
        fn()
    durations = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        durations.append((t1 - t0) * 1000.0)  # ms
    return {
        "mean_ms": round(statistics.mean(durations), 2),
        "median_ms": round(statistics.median(durations), 2),
        "min_ms": round(min(durations), 2),
        "max_ms": round(max(durations), 2),
        "p95_ms": round(sorted(durations)[int(len(durations) * 0.95)], 2),
    }

def run_profiling():
    print("=" * 70)
    print("🚀 STARTING COMPREHENSIVE PERFORMANCE PROFILING PASS")
    print("=" * 70)
    client = TestClient(app)
    results = {}

    # ---------------------------------------------------------
    # 1. FRONTEND INITIAL LOAD
    # ---------------------------------------------------------
    print("\n[1/6] Measuring Frontend Initial Load Latency...")
    fe_routes = [
        ("/", "Landing Page"),
        ("/candidate/upload", "Candidate Upload"),
        ("/candidate/results", "Candidate Results"),
        ("/recruiter", "Recruiter Dashboard"),
        ("/insights", "Market Intelligence Dashboard"),
    ]
    fe_bench = {}
    for path, label in fe_routes:
        try:
            def fetch_page(p=path):
                req = urllib.request.Request(f"http://localhost:3000{p}", headers={"User-Agent": "Benchmark"})
                with urllib.request.urlopen(req, timeout=5) as response:
                    return response.read(), response.getcode()

            content, code = fetch_page()
            stats = benchmark_function(fetch_page, iterations=10, warmup=2)
            stats["status_code"] = code
            stats["content_length_bytes"] = len(content)
            fe_bench[label] = stats
            print(f"  ✓ {label} ({path}): {stats['mean_ms']} ms (Size: {len(content):,} bytes)")
        except Exception as e:
            fe_bench[label] = {"error": str(e)}
            print(f"  ✗ {label} ({path}): Error {e}")
    results["frontend_initial_load"] = fe_bench

    # ---------------------------------------------------------
    # 2. DOCUMENT PARSING (In-Memory Microbenchmarks)
    # ---------------------------------------------------------
    print("\n[2/6] Measuring Document Parsing Directly...")
    pdf_bytes = generate_pdf_bytes(SAMPLE_RESUME_TEXT)
    docx_bytes = generate_docx_bytes(SAMPLE_RESUME_TEXT)
    txt_bytes = SAMPLE_RESUME_TEXT.encode("utf-8")

    pdf_parse_stats = benchmark_function(lambda: parse_document(pdf_bytes, "resume.pdf", "application/pdf"), iterations=25)
    docx_parse_stats = benchmark_function(lambda: parse_document(docx_bytes, "resume.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"), iterations=25)
    txt_parse_stats = benchmark_function(lambda: parse_document(txt_bytes, "resume.txt", "text/plain"), iterations=25)

    print(f"  ✓ PDF Parsing (PyMuPDF): {pdf_parse_stats['mean_ms']} ms (P95: {pdf_parse_stats['p95_ms']} ms)")
    print(f"  ✓ DOCX Parsing (python-docx): {docx_parse_stats['mean_ms']} ms (P95: {docx_parse_stats['p95_ms']} ms)")
    print(f"  ✓ Plain Text Parsing: {txt_parse_stats['mean_ms']} ms (P95: {txt_parse_stats['p95_ms']} ms)")
    results["document_parsing"] = {
        "pdf": pdf_parse_stats,
        "docx": docx_parse_stats,
        "txt": txt_parse_stats,
    }

    # ---------------------------------------------------------
    # 3. RESUME UPLOAD (FastAPI HTTP Multipart Upload)
    # ---------------------------------------------------------
    print("\n[3/6] Measuring Resume Upload HTTP Endpoint (/api/v1/documents/parse)...")
    def upload_pdf():
        client.post(
            "/api/v1/documents/parse",
            files={"file": ("resume.pdf", pdf_bytes, "application/pdf")}
        )
    def upload_docx():
        client.post(
            "/api/v1/documents/parse",
            files={"file": ("resume.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )
    pdf_upload_stats = benchmark_function(upload_pdf, iterations=20)
    docx_upload_stats = benchmark_function(upload_docx, iterations=20)
    print(f"  ✓ PDF Upload & Parse API: {pdf_upload_stats['mean_ms']} ms (P95: {pdf_upload_stats['p95_ms']} ms)")
    print(f"  ✓ DOCX Upload & Parse API: {docx_upload_stats['mean_ms']} ms (P95: {docx_upload_stats['p95_ms']} ms)")
    results["resume_upload_api"] = {
        "pdf_upload": pdf_upload_stats,
        "docx_upload": docx_upload_stats,
    }

    # ---------------------------------------------------------
    # 4. SKILL EXTRACTION & LOOKUP
    # ---------------------------------------------------------
    print("\n[4/6] Measuring Skill Extraction & Taxonomy Lookup...")
    extract_stats = benchmark_function(lambda: extractor.extract_from_text(SAMPLE_RESUME_TEXT), iterations=25)
    # Normalizer single skill lookup
    raw_terms = ["Python", "JS", "React.js", "Docker", "Machine Learning", "Amazon Web Services", "unknown_term_xyz"]
    norm_stats = benchmark_function(lambda: [normalizer.normalize(t) for t in raw_terms], iterations=100)

    print(f"  ✓ Full Resume Skill Extraction: {extract_stats['mean_ms']} ms (P95: {extract_stats['p95_ms']} ms)")
    print(f"  ✓ Batch Skill Term Normalization (7 terms): {norm_stats['mean_ms']} ms")
    report = extractor.extract_from_text(SAMPLE_RESUME_TEXT)
    print(f"    -> Extracted {len(report.skills)} canonical skills from {report.sentences_analyzed} sentences")
    results["skill_extraction"] = {
        "full_extraction": extract_stats,
        "term_normalization": norm_stats,
        "skills_detected": len(report.skills),
    }

    # ---------------------------------------------------------
    # 5. MATCHING ENGINE & RECRUITER BATCH EVALUATION
    # ---------------------------------------------------------
    print("\n[5/6] Measuring Matching Engine & Recruiter Screening...")
    candidate_skills = report.skills
    single_match_stats = benchmark_function(
        lambda: matching_engine.calculate_match(
            candidate_skills=candidate_skills,
            target_role="backend_engineer",
            candidate_experience_years=5.0
        ),
        iterations=50
    )
    # Batch matching: 10 candidates against job description
    candidates_batch = [
        CandidateInputPayload(
            id=f"c_{i}",
            name=f"Candidate {i}",
            candidate_skills=candidate_skills,
            experience_years=4.0
        )
        for i in range(10)
    ]
    batch_match_stats = benchmark_function(
        lambda: recruiter_engine.rank_candidates(
            candidates=candidates_batch,
            job_title="Data Scientist",
            required_skills=["Python", "SQL", "Machine Learning", "Statistics & Probability"],
            preferred_skills=["Docker & Containerization", "AWS"]
        ),
        iterations=20
    )
    # Candidate Pipeline Unified Endpoint
    pipeline_stats = benchmark_function(
        lambda: client.post(
            "/api/v1/matching/candidate-pipeline",
            json={
                "candidate_skills": [s.model_dump() for s in candidate_skills],
                "target_role": "data_scientist",
                "candidate_experience_years": 4.0
            }
        ),
        iterations=20
    )
    print(f"  ✓ Single-Roundtrip Candidate Pipeline: {pipeline_stats['mean_ms']} ms (P95: {pipeline_stats['p95_ms']} ms)")
    results["candidate_pipeline_unified"] = pipeline_stats

    print(f"  ✓ Single Candidate Match Computation: {single_match_stats['mean_ms']} ms (P95: {single_match_stats['p95_ms']} ms)")
    print(f"  ✓ Recruiter Batch Ranking (10 candidates): {batch_match_stats['mean_ms']} ms (P95: {batch_match_stats['p95_ms']} ms)")
    results["matching"] = {
        "single_match": single_match_stats,
        "batch_ranking_10_candidates": batch_match_stats,
        "unified_pipeline": pipeline_stats,
    }

    # ---------------------------------------------------------
    # 6. DASHBOARD RENDERING & API PAYLOAD
    # ---------------------------------------------------------
    print("\n[6/6] Measuring Market Intelligence API & Payload Size...")
    resp = client.get("/api/v1/insights/market-intelligence")
    payload_size_bytes = len(resp.content)
    # Also measure wire size with GZip
    resp_gz = client.get("/api/v1/insights/market-intelligence", headers={"Accept-Encoding": "gzip"})
    dash_stats = benchmark_function(lambda: client.get("/api/v1/insights/market-intelligence"), iterations=25)
    direct_dash_stats = benchmark_function(lambda: get_complete_market_intelligence(), iterations=25)

    print(f"  ✓ Market Intelligence API Endpoint: {dash_stats['mean_ms']} ms (Decompressed: {payload_size_bytes:,} bytes)")
    print(f"  ✓ Market Intelligence Core Computation: {direct_dash_stats['mean_ms']} ms")
    results["dashboard_and_payload"] = {
        "api_endpoint": dash_stats,
        "core_computation": direct_dash_stats,
        "payload_size_bytes": payload_size_bytes,
        "payload_size_kb": round(payload_size_bytes / 1024, 2),
    }

    print("\n" + "=" * 70)
    print("PROFILING SUMMARY COMPLETE")
    print("=" * 70)
    with open("docs/optimized_profile.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Saved optimized measurements to docs/optimized_profile.json")

if __name__ == "__main__":
    run_profiling()
