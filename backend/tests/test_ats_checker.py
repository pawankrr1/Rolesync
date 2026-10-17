"""Automated Tests for ATS Resume Checker (ATS-01 through ATS-10)."""

import io
import pytest
from fastapi.testclient import TestClient
import fitz  # PyMuPDF
from docx import Document

from app.main import app
from app.services.ats_service import ATSService
from app.core.normalizer import normalizer

client = TestClient(app)


def create_sample_pdf_bytes(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


def create_sample_docx_bytes(text: str) -> bytes:
    doc = Document()
    doc.add_paragraph(text)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


SAMPLE_RESUME_TEXT = """Jane Doe
Email: jane@example.com | Phone: +1 555-0199 | LinkedIn: linkedin.com/in/janedoe

PROFESSIONAL SUMMARY
Experienced Software Engineer with 4 years building scalable web architectures.

EXPERIENCE
Software Engineer at GlobalTech (2021 - Present)
- Developed REST microservices with Python, FastAPI, and PostgreSQL, reducing latency by 30%.
- Built automated Docker container deployments with Git workflows for 40,000 active users.
- Designed database schemas and optimized SQL query execution, scaling system throughput by 3x.

EDUCATION
Bachelor of Science in Computer Science, University of Technology

SKILLS
Programming: Python, SQL, JS
Frameworks: FastAPI
DevOps: Docker, Git, Linux
"""


def test_ats_01_valid_pdf_general_analysis():
    """ATS-01: Valid PDF resume -> general ATS analysis."""
    pdf_bytes = create_sample_pdf_bytes(SAMPLE_RESUME_TEXT)
    files = {"file": ("resume.pdf", pdf_bytes, "application/pdf")}
    data = {"check_type": "general"}

    response = client.post("/api/v1/ats/upload-and-analyze", files=files, data=data)
    assert response.status_code == 200
    res = response.json()

    assert res["check_type"] == "general"
    assert 0 <= res["overall_score"] <= 100
    assert res["rating"] in ["Excellent", "Strong", "Good", "Needs Improvement", "Needs Attention"]
    assert len(res["category_scores"]) == 5
    assert any(c["category_id"] == "parseability" for c in res["category_scores"])
    assert any(c["category_id"] == "skills" for c in res["category_scores"])
    assert res["parse_confidence"] in ["High", "Medium"]
    assert len(res["checklist"]) >= 5


def test_ats_02_valid_docx_general_analysis():
    """ATS-02: Valid DOCX resume -> general ATS analysis."""
    docx_bytes = create_sample_docx_bytes(SAMPLE_RESUME_TEXT)
    files = {"file": ("resume.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    data = {"check_type": "general"}

    response = client.post("/api/v1/ats/upload-and-analyze", files=files, data=data)
    assert response.status_code == 200
    res = response.json()

    assert res["check_type"] == "general"
    assert 0 <= res["overall_score"] <= 100
    assert len(res["category_scores"]) == 5


def test_ats_03_resume_plus_jd_job_specific():
    """ATS-03: Resume + JD -> job-specific ATS analysis."""
    payload = {
        "resume_text": SAMPLE_RESUME_TEXT,
        "filename": "resume.pdf",
        "check_type": "job_specific",
        "target_job_title": "Backend Python Engineer",
        "job_description_text": "Looking for Backend Engineer skilled in Python, SQL, and Docker. Experience with AWS is desired.",
    }

    response = client.post("/api/v1/ats/analyze", json=payload)
    assert response.status_code == 200
    res = response.json()

    assert res["check_type"] == "job_specific"
    assert res["target_job_title"] == "Backend Python Engineer"
    assert res["job_alignment_percentage"] is not None
    assert any(c["category_id"] == "job_alignment" for c in res["category_scores"])
    assert res["matched_jd_skills_count"] > 0


def test_ats_04_missing_target_skill():
    """ATS-04: Missing target skill -> appears under missing skills."""
    payload = {
        "resume_text": SAMPLE_RESUME_TEXT,
        "filename": "resume.pdf",
        "check_type": "job_specific",
        "target_job_title": "Data Analyst",
        "job_description_text": "Requirements: Python, SQL, and Power BI dashboards.",
    }

    response = client.post("/api/v1/ats/analyze", json=payload)
    assert response.status_code == 200
    res = response.json()

    missing_names = [m["name"].lower() for m in res["missing_skills"]]
    assert any("power bi" in m for m in missing_names)


def test_ats_05_normalized_alias_resolution():
    """ATS-05: Normalized alias works (JS <-> JavaScript)."""
    norm = normalizer.normalize("JS")
    assert norm.is_resolved is True
    assert norm.canonical_id == "javascript"
    assert norm.canonical_name == "JavaScript"

    # In ATS job-specific check, resume has "JS" and JD has "JavaScript"
    payload = {
        "resume_text": "Skills: Python, JS, SQL\nExperience: Built frontend apps using JS and Python.",
        "filename": "resume.pdf",
        "check_type": "job_specific",
        "job_description_text": "Must know Python and JavaScript.",
    }
    response = client.post("/api/v1/ats/analyze", json=payload)
    assert response.status_code == 200
    res = response.json()

    matched_ids = [m["canonical_name"].lower() for m in res["matched_skills"]]
    assert any("javascript" in m for m in matched_ids)


def test_ats_06_repeated_keywords_no_inflation():
    """ATS-06: Repeated keywords do not inflate score."""
    normal_resume = (
        SAMPLE_RESUME_TEXT
    )
    stuffed_resume = (
        SAMPLE_RESUME_TEXT + "\n\nPython Python Python Python Python Python Python Python Python Python SQL SQL SQL SQL"
    )

    res_normal = ATSService.analyze(resume_text=normal_resume, check_type="general")
    res_stuffed = ATSService.analyze(resume_text=stuffed_resume, check_type="general")

    # Skills presentation score should NOT be higher for spamming keywords
    normal_skills_score = next(c.score for c in res_normal.category_scores if c.category_id == "skills")
    stuffed_skills_score = next(c.score for c in res_stuffed.category_scores if c.category_id == "skills")

    assert stuffed_skills_score <= normal_skills_score


def test_ats_07_unsupported_file():
    """ATS-07: Unsupported file -> useful error."""
    files = {"file": ("malicious.exe", b"MZ\x90\x00\x03fake-executable", "application/x-msdownload")}
    response = client.post("/api/v1/ats/upload-and-analyze", files=files, data={"check_type": "general"})
    assert response.status_code in [400, 415, 422]


def test_ats_08_parsing_failure_no_misleading_score():
    """ATS-08: Parsing failure or empty input -> clean error or low confidence."""
    # Empty resume text
    response = client.post("/api/v1/ats/analyze", json={"resume_text": "   ", "check_type": "general"})
    assert response.status_code == 400

    # Very sparse text -> low parse confidence
    sparse_res = ATSService.analyze(resume_text="Hello world test", check_type="general")
    assert sparse_res.parse_confidence == "Low"


def test_ats_09_deterministic_same_input_same_score():
    """ATS-09: Same input -> same score."""
    run1 = ATSService.analyze(
        resume_text=SAMPLE_RESUME_TEXT,
        check_type="job_specific",
        job_description_text="Python and SQL required.",
    )
    run2 = ATSService.analyze(
        resume_text=SAMPLE_RESUME_TEXT,
        check_type="job_specific",
        job_description_text="Python and SQL required.",
    )

    assert run1.overall_score == run2.overall_score
    assert len(run1.category_scores) == len(run2.category_scores)
    for c1, c2 in zip(run1.category_scores, run2.category_scores):
        assert c1.score == c2.score
        assert c1.percentage == c2.percentage


def test_ats_10_existing_resume_upload_unaffected():
    """ATS-10: Existing resume upload workflow remains unaffected."""
    pdf_bytes = create_sample_pdf_bytes(SAMPLE_RESUME_TEXT)
    files = {"file": ("test.pdf", pdf_bytes, "application/pdf")}

    doc_res = client.post("/api/v1/documents/parse", files=files)
    assert doc_res.status_code == 200
    doc_json = doc_res.json()
    assert "text" in doc_json

    skill_res = client.post("/api/v1/skills/extract", json={"resume_text": doc_json["text"]})
    assert skill_res.status_code == 200
    assert "skills" in skill_res.json()
