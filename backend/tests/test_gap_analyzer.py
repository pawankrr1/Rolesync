"""Comprehensive Test Suite for Skill Gap Analysis Engine.

Validates:
1. Core logic: Required skills minus Candidate skills, improved via taxonomy & demand.
2. Classification into STRONG, PARTIAL, MISSING.
3. For each missing/partial skill: priority, importance, reason, recommended next action.
4. 5-factor priority calculation:
   - Role importance (required vs preferred)
   - Skill demand in available dataset (data/jobs.json)
   - Similarity to candidate's existing skills (taxonomy adjacency)
   - Learning dependency (prerequisites, unblocking)
   - Current gap magnitude
5. Grounded evidence constraint: no external market claims without dataset evidence.
6. Return structure: gap_score, strong_skills, partial_skills, missing_skills, priority_order.
7. API endpoint POST /api/v1/gap/analyze with skills list, resume text, and explicit overrides.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.gap_analyzer import (
    gap_analyzer,
    SkillGapAnalyzer,
    SkillGapItem,
    GapAnalysisReport,
)
from app.core.role_engine import role_engine
from app.core.taxonomy import taxonomy

client = TestClient(app)


# ---------------------------------------------------------------------------
# Test 1: Classification into STRONG, PARTIAL, MISSING
# ---------------------------------------------------------------------------

def test_classification_strong_partial_missing():
    """Verify skills are accurately classified into STRONG, PARTIAL, and MISSING."""
    target_role = role_engine.get_role("backend_engineer")
    assert target_role is not None
    # Backend Engineer requires: Python, SQL, FastAPI, PostgreSQL, Docker, Git

    # Candidate profile:
    # - Python (Direct required -> STRONG)
    # - SQL (Direct required -> STRONG, also adjacent to PostgreSQL)
    # - FastAPI (Direct required -> STRONG)
    # Candidate lacks Docker and Git
    # Candidate lacks PostgreSQL, BUT has SQL which is adjacent to PostgreSQL -> PARTIAL
    # Candidate lacks Docker -> MISSING (no adjacent container skill)
    # Candidate lacks Git -> MISSING (no adjacent version control skill)
    cand_skills = ["Python", "SQL", "FastAPI"]

    report = gap_analyzer.analyze_gaps(
        candidate_skills=cand_skills,
        target_role=target_role
    )

    strong_names = [s.skill for s in report.strong_skills]
    partial_names = [p.skill for p in report.partial_skills]
    missing_names = [m.skill for m in report.missing_skills]

    # Verify STRONG
    assert "Python" in strong_names
    assert "SQL" in strong_names
    assert "FastAPI" in strong_names
    for s in report.strong_skills:
        assert s.classification == "STRONG"
        assert s.priority == "NONE"

    # Verify PARTIAL (PostgreSQL has SQL as adjacent skill in taxonomy)
    assert any("PostgreSQL" in p for p in partial_names)
    for p in report.partial_skills:
        assert p.classification == "PARTIAL"
        assert len(p.adjacent_skills_found) > 0

    # Verify MISSING
    assert any("Docker" in m for m in missing_names)
    assert any("Git" in m for m in missing_names)
    for m in report.missing_skills:
        assert m.classification == "MISSING"


# ---------------------------------------------------------------------------
# Test 2: Required Output Attributes for Missing & Partial Skills
# ---------------------------------------------------------------------------

def test_gap_item_required_attributes():
    """Ensure every gap item calculates priority, importance, reason, and recommended next action."""
    report = gap_analyzer.analyze_gaps(
        candidate_skills=["Python"],
        target_role="backend_engineer"
    )

    all_gaps = report.partial_skills + report.missing_skills
    assert len(all_gaps) > 0

    for gap in all_gaps:
        # Priority: HIGH, MEDIUM, or LOW
        assert gap.priority in ("HIGH", "MEDIUM", "LOW")
        assert gap.priority_score > 0.0

        # Importance: CRITICAL, HIGH, MEDIUM, LOW + numeric
        assert gap.importance in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
        assert gap.importance_score > 0.0

        # Reason: Grounded explainable narrative
        assert isinstance(gap.reason, str)
        assert len(gap.reason) > 15
        assert "target role" in gap.reason.lower() or "dataset" in gap.reason.lower()

        # Recommended Next Action: Actionable next step
        assert isinstance(gap.recommended_next_action, str)
        assert len(gap.recommended_next_action) > 15
        # Must recommend either a course or structured project
        assert any(kw in gap.recommended_next_action.lower() for kw in ("complete", "course", "build", "master", "prototype"))


# ---------------------------------------------------------------------------
# Test 3: Priority Considerations & Ranking
# ---------------------------------------------------------------------------

def test_priority_calculation_dimensions():
    """Verify priority incorporates role importance, dataset demand, dependencies, and similarities."""
    # Data Scientist requires Python, SQL, Statistics, Machine Learning, Pandas, Scikit-Learn
    # Candidate has Python and SQL
    report = gap_analyzer.analyze_gaps(
        candidate_skills=["Python", "SQL"],
        target_role="data_scientist"
    )

    # Priority order must be sorted descending by priority_score
    scores = [g.priority_score for g in report.priority_order]
    assert scores == sorted(scores, reverse=True)

    # Priority ranks must be sequential 1, 2, 3...
    ranks = [g.priority_rank for g in report.priority_order]
    assert ranks == list(range(1, len(report.priority_order) + 1))

    # Top priority gaps should be marked HIGH
    first_gap = report.priority_order[0]
    assert first_gap.priority == "HIGH"
    assert first_gap.priority_score >= 10.0


# ---------------------------------------------------------------------------
# Test 4: Dataset Evidence Constraint (No External Market Claims)
# ---------------------------------------------------------------------------

def test_dataset_evidence_grounding():
    """Verify reasons only reference evidence from the available jobs dataset."""
    report = gap_analyzer.analyze_gaps(
        candidate_skills=["Python"],
        target_role="backend_engineer"
    )

    docker_gap = next((g for g in report.priority_order if "docker" in g.skill_id), None)
    assert docker_gap is not None

    # Docker appears frequently in jobs.json (19 of 50 jobs)
    assert docker_gap.dataset_demand_count > 0
    assert docker_gap.dataset_demand_percentage > 0.0
    # Reason must ground demand in the available dataset without inventing unverified statistics
    assert "available dataset" in docker_gap.reason.lower()
    assert str(docker_gap.dataset_demand_count) in docker_gap.reason or f"{docker_gap.dataset_demand_percentage}%" in docker_gap.reason


# ---------------------------------------------------------------------------
# Test 5: Learning Dependency & Prerequisite Unblocking
# ---------------------------------------------------------------------------

def test_learning_dependency_unblocking():
    """Foundational skills that unblock subsequent requirements receive priority bonus."""
    # If candidate has NO skills, Python unblocks FastAPI, Scikit-Learn, Machine Learning
    report = gap_analyzer.analyze_gaps(
        candidate_skills=[],
        target_role="backend_engineer"
    )

    python_gap = next((g for g in report.priority_order if g.skill_id == "python"), None)
    assert python_gap is not None

    # Python unblocks FastAPI in backend_engineer requirements
    assert python_gap.priority == "HIGH"
    assert "FastAPI" in python_gap.unblocks_skills
    assert "unblocking" in python_gap.reason.lower() or "unblock" in python_gap.reason.lower()


# ---------------------------------------------------------------------------
# Test 6: Gap Score Determinism & Boundary Conditions
# ---------------------------------------------------------------------------

def test_gap_score_boundaries():
    """Verify gap_score behavior across perfect, partial, and empty candidates."""
    target_role = role_engine.get_role("backend_engineer")
    all_reqs = ["Python", "SQL", "PostgreSQL", "FastAPI", "Docker", "Git"]

    # Perfect candidate for core requirements: gap_score == 0.0
    report_perfect = gap_analyzer.analyze_gaps(candidate_skills=all_reqs, target_role=target_role)
    assert report_perfect.gap_score == 0.0
    missing_required = [m for m in report_perfect.missing_skills if m.is_required]
    assert len(missing_required) == 0
    assert len(report_perfect.strong_skills) >= 6

    # Candidate with all required AND preferred skills: zero missing skills
    all_role_skills = all_reqs + ["Redis", "Apache Kafka", "AWS", "System Design & Architecture"]
    report_all = gap_analyzer.analyze_gaps(candidate_skills=all_role_skills, target_role=target_role)
    assert report_all.gap_score == 0.0
    assert len(report_all.missing_skills) == 0
    assert len(report_all.partial_skills) == 0

    # Empty candidate: gap_score == 100.0
    report_empty = gap_analyzer.analyze_gaps(candidate_skills=[], target_role=target_role)
    assert report_empty.gap_score == 100.0
    assert len(report_empty.strong_skills) == 0
    assert len(report_empty.missing_skills) >= 6

    # Partial candidate: 0.0 < gap_score < 100.0
    report_partial = gap_analyzer.analyze_gaps(candidate_skills=["Python", "SQL"], target_role=target_role)
    assert 0.0 < report_partial.gap_score < 100.0
    assert report_partial.gap_score + report_partial.readiness_percentage == 100.0


# ---------------------------------------------------------------------------
# Test 7: API Endpoint POST /api/v1/gap/analyze
# ---------------------------------------------------------------------------

def test_api_gap_analyze_with_skills_list():
    """POST /api/v1/gap/analyze with candidate skills and target role."""
    payload = {
        "candidate_skills": ["Python", "SQL"],
        "target_role": "data_scientist"
    }
    response = client.post("/api/v1/gap/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "gap_score" in data
    assert "strong_skills" in data
    assert "partial_skills" in data
    assert "missing_skills" in data
    assert "priority_order" in data

    assert isinstance(data["gap_score"], float)
    assert len(data["strong_skills"]) >= 2
    assert len(data["priority_order"]) > 0

    first_priority = data["priority_order"][0]
    assert "skill" in first_priority
    assert "classification" in first_priority
    assert "priority" in first_priority
    assert "importance" in first_priority
    assert "reason" in first_priority
    assert "recommended_next_action" in first_priority


def test_api_gap_analyze_with_resume_text():
    """POST /api/v1/gap/analyze extracts skills from raw resume text."""
    payload = {
        "resume_text": "Experienced Python software engineer building microservices with SQL and PostgreSQL databases.",
        "target_role": "backend_engineer"
    }
    response = client.post("/api/v1/gap/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    strong_names = [s["skill"] for s in data["strong_skills"]]
    assert "Python" in strong_names
    assert "PostgreSQL" in strong_names

    # Docker is missing from this resume
    missing_names = [m["skill"] for m in data["missing_skills"]]
    assert any("Docker" in m for m in missing_names)


def test_api_gap_analyze_with_explicit_required_skills():
    """POST /api/v1/gap/analyze with custom explicit requirements."""
    payload = {
        "candidate_skills": ["Python", "SQL"],
        "required_skills": ["Python", "SQL", "Docker", "Kubernetes"],
        "preferred_skills": ["AWS"]
    }
    response = client.post("/api/v1/gap/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert len(data["strong_skills"]) >= 2
    # Docker and Kubernetes are missing
    missing_names = [m["skill"] for m in data["missing_skills"]]
    assert any("Docker" in m for m in missing_names)
    assert any("Kubernetes" in m for m in missing_names)
