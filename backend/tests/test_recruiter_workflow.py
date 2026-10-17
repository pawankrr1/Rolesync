"""Test Suite for Recruiter Screening & Talent Ranking Workflow.

Validates:
1. Job description parsing and required skill extraction
2. Multi-candidate evaluation & ranking by explainable match score
3. Correct structure: candidate, match score, strong skills, missing skills, experience, reason
4. Detailed explanation inspection modal payload (matched, partial, missing)
5. Ethical AI & language guardrails:
   - Does NOT claim highest score means candidate is "best"
   - Uses "Highest measured skill alignment in this dataset."
   - Includes decision support disclaimer (not an automated hiring decision)
6. Fast response and robustness across varying candidate profiles
7. FastAPI endpoint testing for POST /api/v1/recruiter/rank and POST /api/v1/recruiter/parse-jd
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.recruiter_engine import (
    recruiter_engine,
    RecruiterEngine,
    CandidateInputPayload,
    RecruiterRankResponse,
    DISCLAIMER_TEXT,
    TOP_CANDIDATE_STATEMENT,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Test Data Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_jd_text() -> str:
    return (
        "Senior Data Scientist\n"
        "Requirements:\n"
        "We are looking for a Senior Data Scientist with 3+ years experience.\n"
        "Required Skills:\n"
        "- Strong proficiency in Python, SQL, Machine Learning, and Statistics & Probability.\n"
        "- Experience with Pandas and Scikit-Learn for tabular data processing.\n"
        "Preferred Skills:\n"
        "- Familiarity with Cloud architectures, Deep Learning, and Docker is preferred.\n"
    )


@pytest.fixture
def multiple_candidates() -> list[CandidateInputPayload]:
    return [
        # Candidate 1: High Alignment (Matches Python, SQL, Machine Learning, Statistics, Cloud)
        CandidateInputPayload(
            id="cand_pawan",
            name="Pawan Kumar",
            filename="pawan_resume.pdf",
            candidate_skills=["Python", "SQL", "Machine Learning", "Statistics & Probability", "Cloud"],
            experience_years=4.0,
        ),
        # Candidate 2: Moderate Match (Matches Python, SQL, Pandas)
        CandidateInputPayload(
            id="cand_priya",
            name="Priya Patel",
            filename="priya_resume.pdf",
            candidate_skills=["Python", "SQL", "Pandas", "Excel"],
            experience_years=2.5,
        ),
        # Candidate 3: Low / Entry Match (Only SQL, Excel)
        CandidateInputPayload(
            id="cand_junior",
            name="Aditi Sharma",
            filename="aditi_resume.pdf",
            candidate_skills=["SQL", "Excel", "Power BI"],
            experience_years=1.0,
        ),
        # Candidate 4: Unrelated / Minimal Match (Only React, CSS)
        CandidateInputPayload(
            id="cand_web",
            name="Karan Verma",
            filename="karan_resume.pdf",
            candidate_skills=["React.js", "CSS3", "HTML5"],
            experience_years=2.0,
        ),
    ]


# ---------------------------------------------------------------------------
# Test 1: Extract Required Skills from Job Description
# ---------------------------------------------------------------------------

def test_extract_job_skills_from_jd(sample_jd_text):
    """Verify system extracts required and preferred skills from raw JD text."""
    extracted = recruiter_engine.extract_job_skills(sample_jd_text, role_title="Senior Data Scientist")
    
    assert "required_skills" in extracted
    assert "preferred_skills" in extracted
    
    reqs = extracted["required_skills"]
    prefs = extracted["preferred_skills"]
    
    assert len(reqs) > 0
    # Core competencies should be recognized
    all_skills = reqs + prefs
    assert any("Python" in s for s in all_skills)
    assert any("SQL" in s for s in all_skills)
    assert any("Machine Learning" in s for s in all_skills)


# ---------------------------------------------------------------------------
# Test 2: Rank Multiple Candidates
# ---------------------------------------------------------------------------

def test_rank_multiple_candidates(multiple_candidates, sample_jd_text):
    """Verify engine ranks candidates descending by match score with proper attributes."""
    res = recruiter_engine.rank_candidates(
        candidates=multiple_candidates,
        job_description_text=sample_jd_text,
        job_title="Senior Data Scientist",
        required_skills=["Python", "SQL", "Machine Learning", "Statistics & Probability"],
        preferred_skills=["Cloud", "Docker", "Kubernetes"],
    )

    assert isinstance(res, RecruiterRankResponse)
    assert res.total_candidates_evaluated == len(multiple_candidates)
    assert len(res.ranked_candidates) == len(multiple_candidates)

    # 1. Ranks must be 1, 2, 3, 4 strictly ordered
    ranks = [c.rank for c in res.ranked_candidates]
    assert ranks == [1, 2, 3, 4]

    # 2. Scores must be sorted in descending order
    scores = [c.match_score for c in res.ranked_candidates]
    assert scores == sorted(scores, reverse=True)

    # 3. Top candidate must be Pawan Kumar
    top_cand = res.ranked_candidates[0]
    assert top_cand.name == "Pawan Kumar"
    assert top_cand.match_score > 70.0

    # 4. Lowest candidate must be Karan Verma (React/CSS)
    lowest_cand = res.ranked_candidates[-1]
    assert lowest_cand.name == "Karan Verma"
    assert lowest_cand.match_score < 40.0


# ---------------------------------------------------------------------------
# Test 3: Display Attributes for Each Candidate
# ---------------------------------------------------------------------------

def test_candidate_display_attributes(multiple_candidates):
    """Verify each candidate record contains Candidate, Match score, Strong skills, Missing skills, Experience, Reason."""
    res = recruiter_engine.rank_candidates(
        candidates=multiple_candidates,
        job_title="Senior Data Scientist",
        required_skills=["Python", "SQL", "Machine Learning", "Statistics & Probability"],
        preferred_skills=["Cloud", "Docker", "Kubernetes"],
    )

    for c in res.ranked_candidates:
        # Candidate
        assert c.name and len(c.name) > 0
        assert c.filename and len(c.filename) > 0
        assert c.candidate_id and len(c.candidate_id) > 0

        # Match score
        assert isinstance(c.match_score, float)
        assert 0.0 <= c.match_score <= 100.0

        # Strong skills & Missing skills
        assert isinstance(c.strong_skills, list)
        assert isinstance(c.missing_skills, list)
        assert isinstance(c.partial_skills, list)

        # Experience
        assert isinstance(c.experience_years, float)
        assert "yrs" in c.experience_display

        # Reason
        assert isinstance(c.reason, str) and len(c.reason) > 0


# ---------------------------------------------------------------------------
# Test 4: Detailed Explanation Payload (Click Candidate)
# ---------------------------------------------------------------------------

def test_detailed_explanation_payload():
    """Verify prompt example: 91% Match, Matched: ..., Partial: ..., Missing: ..."""
    # Candidate with explicit skills matching the prompt's example
    cand = CandidateInputPayload(
        id="cand_test_example",
        name="Test Data Scientist",
        candidate_skills=["Python", "SQL", "Machine Learning", "Statistics & Probability", "Cloud"],
        experience_years=3.5,
    )

    res = recruiter_engine.rank_candidates(
        candidates=[cand],
        job_title="Senior Data Scientist",
        required_skills=["Python", "SQL", "Machine Learning", "Statistics & Probability", "Kubernetes"],
        preferred_skills=["Cloud"],
    )

    top = res.ranked_candidates[0]
    expl = top.detailed_explanation

    # Matched skills
    assert any("Python" in s for s in expl.matched)
    assert any("SQL" in s for s in expl.matched)
    assert any("Machine Learning" in s for s in expl.matched)
    assert any("Statistics" in s for s in expl.matched)

    # Missing skills: Kubernetes was required but candidate did not have it
    assert any("Kubernetes" in s for s in expl.missing)

    # Score display
    assert "Match" in expl.match_score_display


# ---------------------------------------------------------------------------
# Test 5: Ethical Language Guardrails & Decision Support Disclaimer
# ---------------------------------------------------------------------------

def test_ethical_language_and_disclaimer(multiple_candidates):
    """Strictly verify system:
    1. Does NOT claim the highest score means the candidate is objectively the 'best'
    2. Uses 'Highest measured skill alignment in this dataset.'
    3. Includes decision support disclaimer
    """
    res = recruiter_engine.rank_candidates(
        candidates=multiple_candidates,
        job_title="Senior Data Scientist",
        required_skills=["Python", "SQL", "Machine Learning"],
    )

    # 1. Response level statement
    assert res.top_candidate_statement == TOP_CANDIDATE_STATEMENT
    assert "Highest measured skill alignment in this dataset." in res.top_candidate_statement
    assert "best candidate" not in res.top_candidate_statement.lower()

    # 2. Disclaimer verification
    assert res.disclaimer == DISCLAIMER_TEXT
    assert "decision support" in res.disclaimer.lower()
    assert "not an automated hiring decision" in res.disclaimer.lower()

    # 3. Top candidate item statement
    top_cand = res.ranked_candidates[0]
    assert top_cand.alignment_statement == TOP_CANDIDATE_STATEMENT
    assert "best" not in top_cand.alignment_statement.lower()


# ---------------------------------------------------------------------------
# Test 6: API Endpoints (POST /api/v1/recruiter/rank & parse-jd)
# ---------------------------------------------------------------------------

def test_api_parse_jd_endpoint(sample_jd_text):
    """POST /api/v1/recruiter/parse-jd extracts requirements."""
    response = client.post(
        "/api/v1/recruiter/parse-jd",
        json={
            "job_description_text": sample_jd_text,
            "job_title": "Senior Data Scientist",
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["job_title"] == "Senior Data Scientist"
    assert len(data["required_skills"]) > 0
    assert data["total_skills_extracted"] > 0


def test_api_rank_candidates_endpoint(multiple_candidates, sample_jd_text):
    """POST /api/v1/recruiter/rank accepts multiple candidates and returns leaderboard."""
    payload = {
        "job_title": "Senior Data Scientist",
        "job_description_text": sample_jd_text,
        "required_skills": ["Python", "SQL", "Machine Learning", "Statistics & Probability"],
        "preferred_skills": ["Cloud", "Docker", "Kubernetes"],
        "candidates": [c.model_dump() for c in multiple_candidates],
    }

    response = client.post("/api/v1/recruiter/rank", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "ranked_candidates" in data
    assert len(data["ranked_candidates"]) == len(multiple_candidates)

    top = data["ranked_candidates"][0]
    assert top["rank"] == 1
    assert "name" in top
    assert "match_score" in top
    assert "strong_skills" in top
    assert "missing_skills" in top
    assert "experience_display" in top
    assert "reason" in top
    assert "detailed_explanation" in top

    # Ethical guardrails
    assert "Highest measured skill alignment in this dataset." in data["top_candidate_statement"]
    assert "decision support" in data["disclaimer"].lower()
    assert "best" not in data["top_candidate_statement"].lower()


def test_api_get_demo_candidates():
    """GET /api/v1/recruiter/demo-candidates returns seeded demo applicants."""
    response = client.get("/api/v1/recruiter/demo-candidates")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
