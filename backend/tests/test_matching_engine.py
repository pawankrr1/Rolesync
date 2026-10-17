"""Comprehensive Test Suite for Explainable Matching Engine.

Validates the 7 mandated test cases:
1. Perfect candidate
2. Partial candidate
3. Unrelated candidate
4. Missing required skill
5. Extra skills
6. Ambiguous skill
7. No extracted skills

Also validates:
- Configurable weights
- Mathematical reproducibility (same input = same output)
- Exact skill contribution breakdown
- Structure of explanation objects (skill, status, contribution, evidence)
- Narrative generation (why_match, why_not_match, top_strengths, top_gaps)
- API endpoint POST /api/v1/matching/analyze
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.matching_engine import (
    matching_engine,
    MatchWeights,
    ExplainableMatchResult,
    SkillExplanation
)
from app.core.role_engine import role_engine, CareerRoleProfile, RoleSkillRequirement
from app.core.extractor import ExtractedSkill

client = TestClient(app)


# ---------------------------------------------------------------------------
# Test Case 1: Perfect Candidate
# ---------------------------------------------------------------------------

def test_case_1_perfect_candidate():
    """Perfect candidate with all required skills, preferred skills, matching experience and education."""
    target_role = role_engine.get_role("data_scientist")
    assert target_role is not None

    # Candidate has all 6 required skills + all 5 preferred skills
    cand_skills = [
        "Python", "SQL", "Statistics", "Machine Learning", "Pandas", "Scikit-Learn",
        "Deep Learning", "NLP", "Docker", "AWS", "Data Visualization"
    ]
    # Experience: 4 years (role requires 3), Master's degree
    result = matching_engine.calculate_match(
        candidate_skills=cand_skills,
        target_role=target_role,
        candidate_experience_years=4.0,
        candidate_education={"degree": "M.S.", "field": "Computer Science", "level": "master"}
    )

    assert result.final_match_score >= 95.0
    assert result.score_grade == "Exceptional Match"
    assert result.required_skill_coverage == 100.0
    assert result.preferred_skill_coverage == 100.0
    assert result.semantic_similarity >= 90.0
    assert result.experience_alignment >= 90.0

    # No missing required skills
    assert len(result.missing_skills) == 0
    assert len(result.partial_matches) == 0
    assert len(result.strong_matches) >= 11
    assert len(result.top_gaps) == 0
    assert len(result.top_strengths) > 0

    # Explanations
    assert any("Strong direct match on core requirements" in r for r in result.why_match)
    assert any("Bonus preferred skills" in r for r in result.why_match)


# ---------------------------------------------------------------------------
# Test Case 2: Partial Candidate
# ---------------------------------------------------------------------------

def test_case_2_partial_candidate():
    """Partial candidate who possesses some required skills and adjacent skills for others."""
    # Data Scientist requires: Python, SQL, Statistics, Machine Learning, Pandas, Scikit-Learn
    # Candidate has: Python, SQL, but has 'Data Analysis' and 'NumPy' instead of Statistics and Pandas
    cand_skills = ["Python", "SQL", "Data Analysis", "NumPy"]

    target_role = role_engine.get_role("data_scientist")
    result = matching_engine.calculate_match(
        candidate_skills=cand_skills,
        target_role=target_role,
        candidate_experience_years=2.0
    )

    # Moderate score
    assert 40.0 <= result.final_match_score <= 75.0
    assert result.score_grade in ("Moderate Potential", "High Alignment")

    # Has partial matches identified through taxonomy adjacency
    assert len(result.partial_matches) > 0
    partial_names = [p.skill for p in result.partial_matches]
    # Either Pandas (adjacent to NumPy) or Statistics (adjacent to Data Analysis)
    assert any(p in ("Pandas", "Statistics & Probability", "Machine Learning") for p in partial_names)

    # Missing skills identified
    assert len(result.missing_skills) > 0
    assert any("Partial match" in r for r in result.why_match)


# ---------------------------------------------------------------------------
# Test Case 3: Unrelated Candidate
# ---------------------------------------------------------------------------

def test_case_3_unrelated_candidate():
    """Candidate with skills completely outside the role domain (e.g. Sales, Cold Calling)."""
    target_role = role_engine.get_role("ml_engineer")
    cand_skills = ["Technical Communication & Leadership", "Agile & Scrum"]

    result = matching_engine.calculate_match(
        candidate_skills=cand_skills,
        target_role=target_role,
        candidate_experience_years=1.0
    )

    # Score must be very low
    assert result.final_match_score < 25.0
    assert result.score_grade == "Needs Upskilling"
    assert result.required_skill_coverage == 0.0
    assert len(result.missing_skills) >= len(target_role.required_skills)
    assert len(result.strong_matches) == 0

    # Negative narratives explain domain mismatch
    assert any("Missing core required skills" in r for r in result.why_not_match)


# ---------------------------------------------------------------------------
# Test Case 4: Missing Required Skill
# ---------------------------------------------------------------------------

def test_case_4_missing_required_skill():
    """Candidate has all skills EXCEPT 1 critical required skill; score drops predictably."""
    target_role = role_engine.get_role("backend_engineer")
    # Backend Engineer requires: Python, SQL, PostgreSQL, FastAPI, Docker & Containerization, Git & Version Control
    all_reqs = ["Python", "SQL", "PostgreSQL", "FastAPI", "Docker", "Git"]
    # Candidate lacks 'Git' (a core required skill with no adjacent skills present)
    cand_skills_without_git = ["Python", "SQL", "PostgreSQL", "FastAPI", "Docker"]

    result_full = matching_engine.calculate_match(
        candidate_skills=all_reqs,
        target_role=target_role,
        candidate_experience_years=3.0
    )

    result_missing = matching_engine.calculate_match(
        candidate_skills=cand_skills_without_git,
        target_role=target_role,
        candidate_experience_years=3.0
    )

    # Score of candidate missing git must be strictly lower
    assert result_missing.final_match_score < result_full.final_match_score
    diff = result_full.final_match_score - result_missing.final_match_score
    # Drop should be proportional to Git weight (approx 6-20 pts)
    assert 6.0 <= diff <= 20.0

    # Git must be in top_gaps
    assert any("Git" in g for g in result_missing.top_gaps)
    # Missing required details
    missing_names = [m.skill for m in result_missing.missing_skills]
    assert any("Git" in m for m in missing_names)


# ---------------------------------------------------------------------------
# Test Case 5: Extra Skills
# ---------------------------------------------------------------------------

def test_case_5_extra_skills():
    """Extra skills must not penalize the candidate; they enhance domain breadth."""
    target_role = role_engine.get_role("backend_engineer")
    base_skills = ["Python", "SQL", "PostgreSQL", "FastAPI", "Docker"]
    extra_skills = base_skills + ["Kubernetes", "Redis", "Terraform", "AWS", "Git", "TypeScript"]

    result_base = matching_engine.calculate_match(
        candidate_skills=base_skills,
        target_role=target_role,
        candidate_experience_years=3.0
    )

    result_extra = matching_engine.calculate_match(
        candidate_skills=extra_skills,
        target_role=target_role,
        candidate_experience_years=3.0
    )

    # Candidate with extra skills should score equal to or higher than base
    assert result_extra.final_match_score >= result_base.final_match_score
    assert result_extra.required_skill_coverage == 100.0
    assert result_extra.semantic_similarity >= result_base.semantic_similarity


# ---------------------------------------------------------------------------
# Test Case 6: Ambiguous Skill Handling
# ---------------------------------------------------------------------------

def test_case_6_ambiguous_skill_handling():
    """Ambiguous non-technical text must not produce false skill matches."""
    target_role = role_engine.get_role("backend_engineer")

    # Ambiguous English text using verbs "go", "rest", "excel"
    ambiguous_resume = (
        "I will go to the office tomorrow morning to discuss the rest of the project. "
        "I strive to excel in client presentations and take a rest on weekends."
    )

    # Use the live API endpoint which parses raw text through extractor
    res_ambiguous = client.post("/api/v1/matching/analyze", json={
        "resume_text": ambiguous_resume,
        "target_role": "backend_engineer",
        "candidate_experience_years": 0
    })
    assert res_ambiguous.status_code == 200
    data_amb = res_ambiguous.json()

    # Zero false matches
    assert data_amb["final_match_score"] == 0.0
    assert data_amb["required_skill_coverage"] == 0.0

    # Genuine technical resume with Go, REST, Excel, Python, FastAPI, Docker
    tech_resume = (
        "Senior Backend engineer building microservices in Python, Go (Golang), and RESTful APIs. "
        "Experienced in FastAPI, PostgreSQL, Docker, and Microsoft Excel modeling."
    )
    res_tech = client.post("/api/v1/matching/analyze", json={
        "resume_text": tech_resume,
        "target_role": "backend_engineer",
        "candidate_experience_years": 3.0
    })
    assert res_tech.status_code == 200
    data_tech = res_tech.json()

    assert data_tech["final_match_score"] > 60.0
    assert data_tech["required_skill_coverage"] > 50.0


# ---------------------------------------------------------------------------
# Test Case 7: No Extracted Skills
# ---------------------------------------------------------------------------

def test_case_7_no_extracted_skills():
    """Candidate with empty skill profile must receive a deterministic score of 0.0%."""
    target_role = role_engine.get_role("backend_engineer")

    result = matching_engine.calculate_match(
        candidate_skills=[],
        target_role=target_role,
        candidate_experience_years=0.0
    )

    assert result.final_match_score == 0.0
    assert result.overall_match_score == 0.0
    assert result.score_grade == "Needs Upskilling"
    assert result.required_skill_coverage == 0.0
    assert result.preferred_skill_coverage == 0.0
    assert result.semantic_similarity == 0.0
    assert result.experience_alignment == 0.0

    assert len(result.strong_matches) == 0
    assert len(result.top_strengths) == 0
    assert len(result.missing_skills) == len(target_role.required_skills) + len(target_role.preferred_skills)
    assert any("No verified skills detected" in r for r in result.why_not_match)


# ---------------------------------------------------------------------------
# Reproducibility & Mathematical Explainability Tests
# ---------------------------------------------------------------------------

def test_reproducibility_same_input_same_output():
    """Identical inputs must yield identical match scores across multiple executions."""
    skills = ["Python", "SQL", "Docker", "FastAPI"]
    role = "backend_engineer"

    res1 = matching_engine.calculate_match(skills, target_role=role, candidate_experience_years=3.0)
    res2 = matching_engine.calculate_match(skills, target_role=role, candidate_experience_years=3.0)

    assert res1.final_match_score == res2.final_match_score
    assert res1.required_skill_coverage == res2.required_skill_coverage
    assert res1.semantic_similarity == res2.semantic_similarity
    assert res1.experience_alignment == res2.experience_alignment
    assert len(res1.all_skill_explanations) == len(res2.all_skill_explanations)
    for e1, e2 in zip(res1.all_skill_explanations, res2.all_skill_explanations):
        assert e1.contribution == e2.contribution
        assert e1.status == e2.status


def test_configurable_weights():
    """Verify weights alter component contributions mathematically."""
    skills = ["Python", "SQL"]  # Has required skills, low experience
    role = "backend_engineer"

    # Default weights: 60% required, 20% semantic, 10% exp, 10% pref
    res_default = matching_engine.calculate_match(
        skills, target_role=role, candidate_experience_years=0.0
    )

    # Heavily emphasize required skill coverage (90%) and zero experience (0%)
    custom_w = MatchWeights(
        required_coverage=0.90,
        semantic_similarity=0.10,
        experience_alignment=0.0,
        preferred_coverage=0.0
    )
    res_custom = matching_engine.calculate_match(
        skills, target_role=role, custom_weights=custom_w, candidate_experience_years=0.0
    )

    assert res_custom.weights_used.required_coverage == 0.90
    assert res_custom.weights_used.experience_alignment == 0.0
    # Custom score should be higher because 0 years exp is no longer penalized at 10%
    assert res_custom.final_match_score != res_default.final_match_score


def test_explanation_object_schema():
    """Verify explanation objects adhere strictly to the required specification."""
    skills = ["Python", "SQL", "Docker"]
    res = matching_engine.calculate_match(skills, target_role="backend_engineer", candidate_experience_years=2.0)

    for expl in res.all_skill_explanations:
        assert isinstance(expl.skill, str)
        assert expl.status in ("matched", "partial", "missing")
        assert isinstance(expl.contribution, float)
        assert 0.0 <= expl.contribution <= 1.0
        assert isinstance(expl.evidence, str)
        assert len(expl.evidence) > 0


# ---------------------------------------------------------------------------
# API Endpoint Tests: POST /api/v1/matching/analyze
# ---------------------------------------------------------------------------

def test_api_matching_analyze_with_skills_list():
    """POST /api/v1/matching/analyze with direct skills list and role."""
    payload = {
        "candidate_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "SQL", "Git"],
        "target_role": "backend_engineer",
        "candidate_experience_years": 3.0
    }
    response = client.post("/api/v1/matching/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "final_match_score" in data
    assert "required_skill_coverage" in data
    assert "strong_matches" in data
    assert "missing_skills" in data
    assert "why_match" in data
    assert "why_not_match" in data
    assert "top_strengths" in data
    assert "top_gaps" in data

    assert data["final_match_score"] >= 80.0
    assert len(data["strong_matches"]) >= 5

    # Verify explanation object keys
    first_match = data["strong_matches"][0]
    assert "skill" in first_match
    assert "status" in first_match
    assert "contribution" in first_match
    assert "evidence" in first_match


def test_api_matching_analyze_with_custom_weights():
    """POST /api/v1/matching/analyze with custom weights."""
    payload = {
        "candidate_skills": ["Python", "SQL"],
        "target_role": "data_scientist",
        "weights": {
            "required_coverage": 0.80,
            "semantic_similarity": 0.10,
            "experience_alignment": 0.05,
            "preferred_coverage": 0.05
        }
    }
    response = client.post("/api/v1/matching/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["weights_used"]["required_coverage"] == 0.80
    assert data["weights_used"]["semantic_similarity"] == 0.10


def test_api_matching_analyze_with_explicit_required_skills():
    """POST /api/v1/matching/analyze with explicit required skills list."""
    payload = {
        "candidate_skills": ["Python", "Docker"],
        "required_skills": ["Python", "Docker", "Java"],
        "preferred_skills": ["AWS"],
        "candidate_experience_years": 2.0
    }
    response = client.post("/api/v1/matching/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert len(data["strong_matches"]) >= 2
    # Java is completely missing (not adjacent to Python/Docker)
    assert any("Java" in m["skill"] for m in data["missing_skills"])
    assert any("Java" in g for g in data["top_gaps"])
    # AWS has partial credit via Docker
    assert any("AWS" in m["skill"] or "Amazon" in m["skill"] for m in data["partial_matches"])
