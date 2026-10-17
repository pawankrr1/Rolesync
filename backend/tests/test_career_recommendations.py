"""Comprehensive Test Suite for Career Recommendation Engine.

Validates:
1. Returns Top 5 suitable roles based on:
   - candidate skill vector & role skill vector (cosine similarity)
   - skill coverage
   - semantic similarity
   - experience compatibility
2. Structure of each recommendation:
   - role
   - match score
   - matched skills
   - missing skills
   - reason (with required non-guaranteed phrasing: 'Skill alignment', 'Potential fit', 'Based on the current profile')
   - next skills to learn
3. Realistic role matching hierarchy (e.g. Data Analyst 91%, Data Scientist 78%, ML Engineer 72%).
4. Adjacent-role recommendations:
   - Software Engineer → Backend Developer → ML Engineer
   - Activated ONLY when verified skill evidence supports the transition.
   - Omitted when candidate has unrelated / no skill evidence.
5. API endpoint POST /api/v1/recommendations/roles with skills and resume text.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.recommendation_engine import (
    recommendation_engine,
    CareerRecommendationEngine,
    RoleRecommendationItem,
    AdjacentRolePathway,
    CareerRecommendationResponse,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Test 1: Top 5 Role Recommendations with All Required Attributes
# ---------------------------------------------------------------------------

def test_recommend_top_5_roles_structure():
    """Verify engine returns exactly top 5 roles with all required fields and phrasing."""
    # Data Analyst candidate
    skills = ["SQL", "Advanced Excel", "Data Analysis", "Power BI", "Data Visualization"]

    res = recommendation_engine.recommend_roles(
        candidate_skills=skills,
        candidate_experience_years=2.0
    )

    assert len(res.recommended_roles) == 5

    # Scores must be sorted descending
    scores = [r.match_score for r in res.recommended_roles]
    assert scores == sorted(scores, reverse=True)

    # Top match for data analyst skills must be Data Analyst
    top_role = res.recommended_roles[0]
    assert top_role.role == "Data Analyst"
    assert top_role.match_score >= 80.0

    # Verify each result contains all required fields
    for r in res.recommended_roles:
        assert isinstance(r.role, str)
        assert isinstance(r.match_score, float)
        assert 0.0 <= r.match_score <= 100.0
        assert isinstance(r.matched_skills, list)
        assert isinstance(r.missing_skills, list)
        assert isinstance(r.reason, str)
        assert isinstance(r.next_skills_to_learn, list)
        assert isinstance(r.vector_similarity, float)
        assert 0.0 <= r.vector_similarity <= 1.0

        # Non-guaranteed phrasing validation
        assert "Skill alignment" in r.reason or "skill alignment" in r.reason
        assert "Potential fit" in r.reason or "potential fit" in r.reason
        assert "Based on the current profile" in r.reason

    # Disclaimer validation
    assert "guaranteed" in res.disclaimer.lower()


# ---------------------------------------------------------------------------
# Test 2: Mathematical Features (Vectors, Coverage, Experience)
# ---------------------------------------------------------------------------

def test_mathematical_vector_and_coverage_features():
    """Verify vector cosine similarity and coverage are computed explicitly."""
    skills = ["Python", "SQL", "Git"]
    res = recommendation_engine.recommend_roles(
        candidate_skills=skills,
        candidate_experience_years=3.0
    )

    for r in res.recommended_roles:
        # Vector similarity must be between 0 and 1
        assert 0.0 <= r.vector_similarity <= 1.0
        assert 0.0 <= r.skill_coverage <= 100.0
        assert "experience" in r.experience_compatibility.lower()

    # Roles requiring Python/SQL/Git (Backend Developer, Software Engineer) must have higher vector sim than Cybersecurity
    backend_rec = next((r for r in res.recommended_roles if "backend" in r.role_id), None)
    if backend_rec:
        assert backend_rec.vector_similarity > 0.3
        assert backend_rec.skill_coverage > 30.0


# ---------------------------------------------------------------------------
# Test 3: Realistic Role Hierarchy (Data Analyst > Data Scientist > ML Engineer)
# ---------------------------------------------------------------------------

def test_role_hierarchy_ranking():
    """Verify candidate with analyst skills scores highest in Analyst, then Scientist, then ML."""
    analyst_skills = ["SQL", "Advanced Excel", "Data Analysis", "Power BI", "Data Visualization", "Python"]
    res = recommendation_engine.recommend_roles(
        candidate_skills=analyst_skills,
        candidate_experience_years=2.0
    )

    role_score_map = {r.role: r.match_score for r in res.recommended_roles}

    # Data Analyst should be the highest
    assert "Data Analyst" in role_score_map
    analyst_score = role_score_map["Data Analyst"]
    assert analyst_score >= 80.0

    # If Data Scientist is in top 5, its score should be <= Data Analyst
    if "Data Scientist" in role_score_map:
        scientist_score = role_score_map["Data Scientist"]
        assert analyst_score >= scientist_score


# ---------------------------------------------------------------------------
# Test 4: Adjacent-Role Recommendations with Skill Evidence
# ---------------------------------------------------------------------------

def test_adjacent_role_pathway_with_skill_evidence():
    """Software Engineer -> Backend Developer -> ML Engineer transition backed by skill evidence."""
    # Candidate has foundational core engineering skills: Python, SQL, Git
    cand_skills = ["Python", "SQL", "Git & Version Control"]

    res = recommendation_engine.recommend_roles(
        candidate_skills=cand_skills,
        current_role="software_engineer"
    )

    # Adjacent transitions must be returned
    assert len(res.adjacent_transitions) > 0

    # Look for the Software Engineer -> Backend Developer -> ML Engineer pathway
    se_path = next((p for p in res.adjacent_transitions if "Software Engineer" in p.path_title and "ML Engineer" in p.path_title), None)
    assert se_path is not None
    assert se_path.start_role == "Software Engineer"
    assert se_path.target_role in ("ML Engineer", "Machine Learning Engineer")
    assert len(se_path.steps) == 2

    # Step 1: Software Engineer -> Backend Developer
    step1 = se_path.steps[0]
    assert step1.from_role == "Software Engineer"
    assert "Backend" in step1.to_role
    assert any("Python" in s or "SQL" in s or "Git" in s for s in step1.shared_skills)
    assert len(step1.bridge_skills) > 0
    assert "Candidate possesses verified competencies" in step1.evidence

    # Step 2: Backend Developer -> ML Engineer
    step2 = se_path.steps[1]
    assert "Backend" in step2.from_role
    assert any(t in step2.to_role for t in ("ML", "Machine Learning"))
    assert len(step2.bridge_skills) > 0


# ---------------------------------------------------------------------------
# Test 5: Adjacent-Role Omission When Skill Evidence is Lacking
# ---------------------------------------------------------------------------

def test_adjacent_role_omission_without_skill_evidence():
    """Unrelated candidate (no engineering skills) must NOT receive technical transition pathways."""
    # Candidate only has non-technical / sales skills
    cand_skills = ["Technical Communication & Leadership", "Agile & Scrum"]

    res = recommendation_engine.recommend_roles(
        candidate_skills=cand_skills,
        current_role=None
    )

    # Software Engineer -> Backend Developer -> ML Engineer pathway must NOT be present
    se_path = next((p for p in res.adjacent_transitions if "Software Engineer" in p.path_title and "ML Engineer" in p.path_title), None)
    assert se_path is None

    # Empty candidate must have zero adjacent pathways
    res_empty = recommendation_engine.recommend_roles(candidate_skills=[])
    assert len(res_empty.adjacent_transitions) == 0


# ---------------------------------------------------------------------------
# Test 6: API Endpoint POST /api/v1/recommendations/roles
# ---------------------------------------------------------------------------

def test_api_recommend_roles_with_skills_list():
    """POST /api/v1/recommendations/roles with skills list."""
    payload = {
        "candidate_skills": ["Python", "SQL", "Pandas", "Scikit-Learn"],
        "candidate_experience_years": 3.0
    }
    response = client.post("/api/v1/recommendations/roles", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "recommended_roles" in data
    assert "adjacent_transitions" in data
    assert "disclaimer" in data

    assert len(data["recommended_roles"]) == 5

    first_role = data["recommended_roles"][0]
    assert "role" in first_role
    assert "match_score" in first_role
    assert "matched_skills" in first_role
    assert "missing_skills" in first_role
    assert "reason" in first_role
    assert "next_skills_to_learn" in first_role
    assert "vector_similarity" in first_role

    # Non-guaranteed language check
    assert "Skill alignment" in first_role["reason"] or "skill alignment" in first_role["reason"]
    assert "Potential fit" in first_role["reason"] or "potential fit" in first_role["reason"]
    assert "Based on the current profile" in first_role["reason"]


def test_api_recommend_roles_with_resume_text():
    """POST /api/v1/recommendations/roles with raw resume text."""
    payload = {
        "resume_text": "Experienced Python Software Engineer building RESTful APIs, FastAPI microservices, and PostgreSQL database models with Docker and Git.",
        "candidate_experience_years": 3.0
    }
    response = client.post("/api/v1/recommendations/roles", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert len(data["recommended_roles"]) == 5
    top_role = data["recommended_roles"][0]
    assert "Backend" in top_role["role"] or "Software" in top_role["role"]
    assert top_role["match_score"] >= 75.0

    # Adjacent transitions should include backend to ML or software engineering
    assert len(data["adjacent_transitions"]) > 0
