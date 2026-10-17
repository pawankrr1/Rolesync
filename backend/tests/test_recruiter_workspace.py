"""Unit & Integration Tests for Upgraded Recruiter Hiring Intelligence Workspace."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import get_db, SessionLocal, create_all_tables
from app.db.repositories.job_repo import job_repo
from app.db.repositories.shortlist_repo import shortlist_repo
from app.core.recruiter_engine import recruiter_engine, CandidateInputPayload


@pytest.fixture(scope="module")
def client():
    create_all_tables()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_recruiter_overview_metrics(client):
    """Verifies that recruiter overview metrics endpoint returns structured data."""
    res = client.get("/api/v1/recruiter/overview-metrics")
    assert res.status_code == 200
    data = res.json()
    assert "open_roles_count" in data
    assert "candidates_analyzed_count" in data
    assert "strong_matches_count" in data
    assert "average_alignment_percentage" in data
    assert data["is_sample_dataset"] is True


def test_create_and_persist_job(client, db_session):
    """Verifies creating and persisting a new job with required & preferred skills."""
    payload = {
        "title": "Lead MLOps Engineer (Automated Test)",
        "company": "RoleSync Systems",
        "location": "Bengaluru",
        "experience_years_min": 3,
        "description": "Seeking an MLOps engineer with Python, Docker, Kubernetes, and Machine Learning expertise.",
        "required_skills": ["Python", "Docker", "Machine Learning"],
        "preferred_skills": ["Kubernetes", "AWS"],
        "employment_type": "Full-time",
    }
    res = client.post("/api/v1/recruiter/jobs", json=payload)
    assert res.status_code == 201
    data = res.json()
    job_id = data["id"]
    assert data["title"] == payload["title"]
    assert "Python" in data["required_skills"]
    assert "Kubernetes" in data["preferred_skills"]

    # Verify retrieval
    get_res = client.get(f"/api/v1/recruiter/jobs/{job_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == payload["title"]

    # Cleanup
    del_res = client.delete(f"/api/v1/recruiter/jobs/{job_id}")
    assert del_res.status_code == 200


def test_parse_job_description(client):
    """Verifies parsing a raw JD text to extract and separate required vs preferred competencies."""
    jd_text = (
        "We are looking for a Data Analyst with strong SQL, Python, Excel, and statistical analysis skills. "
        "Experience with Power BI and Tableau for dashboards is preferred."
    )
    res = client.post("/api/v1/recruiter/parse-jd", json={"job_description_text": jd_text, "job_title": "Data Analyst"})
    assert res.status_code == 200
    data = res.json()
    assert data["total_skills_extracted"] > 0
    assert any("sql" in s.lower() for s in data["required_skills"])
    assert any("python" in s.lower() for s in data["required_skills"])


def test_candidate_ranking_with_evidence_and_hiring_risk(client):
    """Verifies deterministic 4-factor candidate ranking with authentic evidence and risk calculation."""
    res = client.post(
        "/api/v1/recruiter/rank",
        json={
            "job_title": "Data Analyst",
            "required_skills": ["SQL", "Python", "Excel", "Statistics & Probability"],
            "preferred_skills": ["Power BI"],
            "target_experience_years": 2.0,
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["ranked_candidates"]) > 0

    top = data["ranked_candidates"][0]
    assert "match_score" in top
    assert "hiring_risk" in top
    assert top["hiring_risk"]["level"] in ["LOW RISK", "MEDIUM RISK", "HIGH RISK"]
    assert "detailed_explanation" in top
    assert len(top["detailed_explanation"]["factor_breakdown"]) == 4

    # Check evidence structure
    evidence_list = top["detailed_explanation"]["evidence_list"]
    assert isinstance(evidence_list, list)
    if evidence_list:
        assert "evidence" in evidence_list[0]
        assert "status" in evidence_list[0]


def test_candidate_comparison_with_deterministic_recommendation(client):
    """Verifies comparing candidates side-by-side with deterministic recommendation."""
    res = client.post(
        "/api/v1/recruiter/compare",
        json={
            "candidate_ids": ["cand_demo_01", "cand_demo_02"],
            "job_title": "Data Analyst",
            "required_skills": ["SQL", "Python", "Excel", "Statistics & Probability"],
            "preferred_skills": ["Power BI"],
            "target_experience_years": 2.0,
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["candidates"]) == 2
    assert "recommended_candidate_id" in data
    assert "recommendation_reason" in data
    assert "Highest required-skill coverage" in data["recommendation_reason"]


def test_shortlist_crud_lifecycle(client):
    """Verifies full shortlist lifecycle: add, update stage, query, and remove."""
    cand_id = "test_cand_shortlist_01"
    # 1. Add
    add_res = client.post(
        f"/api/v1/recruiter/candidates/{cand_id}/shortlist",
        json={
            "candidate_id": cand_id,
            "candidate_name": "Test Shortlist Candidate",
            "job_title": "Software Engineer",
            "match_score": 88.0,
            "status": "Shortlisted",
        }
    )
    assert add_res.status_code == 200
    shortlist_item = add_res.json()
    shortlist_id = shortlist_item["id"]

    # 2. Update status to Interview
    patch_res = client.patch(
        f"/api/v1/recruiter/shortlist/{shortlist_id}/status",
        json={"status": "Interview", "notes": "Passed initial screening."}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "Interview"

    # 3. List
    list_res = client.get("/api/v1/recruiter/shortlist")
    assert list_res.status_code == 200
    assert any(item["candidate_id"] == cand_id for item in list_res.json())

    # 4. Remove
    del_res = client.delete(f"/api/v1/recruiter/candidates/{cand_id}/shortlist")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True


def test_recruiter_insights_skill_coverage(client):
    """Verifies applicant pool skill coverage and shortage identification."""
    res = client.get("/api/v1/recruiter/insights?role_title=Data%20Analyst")
    assert res.status_code == 200
    data = res.json()
    assert "skill_coverage" in data
    assert len(data["skill_coverage"]) > 0
    assert "shortage_insight_narrative" in data
    assert data["is_sample_dataset"] is True


def test_talent_pool_query_and_search(client):
    """Verifies querying and filtering the global talent pool."""
    res = client.get("/api/v1/recruiter/talent-pool?skill=python")
    assert res.status_code == 200
    data = res.json()
    assert "candidates" in data
    assert data["total_count"] > 0
    # Every candidate returned should have python
    for c in data["candidates"]:
        assert "python" in [s.lower() for s in c.get("skills", [])]
