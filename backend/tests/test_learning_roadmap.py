"""Comprehensive Test Suite for Learning Roadmap Engine.

Validates:
1. Input handling: candidate profile, target role, missing skills, partial skills.
2. Output format: prioritized learning plan with:
   - skill
   - priority
   - reason
   - prerequisites
   - recommended sequence (1, 2, 3...)
   - estimated learning stage
   - available learning resources from local seeded course dataset
3. Specific prompt case:
   - 1. Statistics (Priority: HIGH, Reason: Required for target role.)
   - 2. Deep Learning (Priority: HIGH, Prerequisite: Machine Learning)
   - 3. Cloud (Priority: MEDIUM)
4. Resource integrity constraint:
   - Do not invent course URLs.
   - Use only seeded resources.
   - If external data unavailable, show 'Demo learning resource' instead of fabricating a real course.
5. Dependency-aware sequencing:
   - Prerequisites are scheduled before dependent skills.
6. API endpoint POST /api/v1/recommendations/roadmap.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.roadmap_generator import (
    roadmap_generator,
    RoadmapGenerator,
    LearningRoadmapResponse,
    LearningRoadmapItem,
    CourseResourceItem,
    SEEDED_COURSES,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Test 1: Full Roadmap Generation from Profile and Role
# ---------------------------------------------------------------------------

def test_roadmap_generation_all_required_attributes():
    """Verify each milestone contains all mandatory attributes."""
    candidate_skills = ["Python", "SQL"]
    target_role = "data_scientist"

    res = roadmap_generator.generate_roadmap(
        candidate_skills=candidate_skills,
        target_role=target_role,
    )

    assert isinstance(res, LearningRoadmapResponse)
    assert len(res.roadmap) > 0
    assert len(res.prioritized_learning_plan) == len(res.roadmap)

    # Sequence numbers must be strictly sequential 1, 2, 3...
    seqs = [item.recommended_sequence for item in res.roadmap]
    assert seqs == list(range(1, len(res.roadmap) + 1))

    for item in res.roadmap:
        # Mandatory fields
        assert isinstance(item.skill, str) and len(item.skill) > 0
        assert item.priority in ("HIGH", "MEDIUM", "LOW")
        assert isinstance(item.reason, str) and len(item.reason) > 0
        assert isinstance(item.prerequisites, list)
        assert isinstance(item.recommended_sequence, int)
        assert isinstance(item.estimated_learning_stage, str)
        assert len(item.estimated_learning_stage) > 0
        assert isinstance(item.available_learning_resources, list)
        assert len(item.available_learning_resources) > 0

        # Stages must follow a logical pedagogical hierarchy
        assert any(stage_kw in item.estimated_learning_stage for stage_kw in ("Foundational", "Core", "Specialization", "Stage"))


# ---------------------------------------------------------------------------
# Test 2: Prompt Example Sequencing (Statistics -> Deep Learning -> Cloud)
# ---------------------------------------------------------------------------

def test_prompt_example_prioritized_sequence():
    """Validates the exact example scenario from the prompt specification.
    
    1. Statistics (Priority: HIGH, Reason: Required for target role.)
    2. Deep Learning (Priority: HIGH, Prerequisite: Machine Learning)
    3. Cloud (Priority: MEDIUM)
    """
    # Candidate starting with Python
    candidate_skills = ["Python"]
    
    # Explicit gaps matching the prompt example
    explicit_missing = ["Statistics", "Deep Learning", "Cloud"]

    res = roadmap_generator.generate_roadmap(
        candidate_skills=candidate_skills,
        target_role="data_scientist",
        missing_skills=explicit_missing,
    )

    skill_names = [item.skill for item in res.roadmap]
    assert any("Statistics" in s for s in skill_names)
    assert any("Deep Learning" in s for s in skill_names)
    assert any("Cloud" in s for s in skill_names)

    # 1. Statistics must be HIGH priority and required for target role
    stats_item = next(item for item in res.roadmap if "Statistics" in item.skill)
    assert stats_item.priority == "HIGH"
    assert "required" in stats_item.reason.lower()

    # 2. Deep Learning must be HIGH priority and list Machine Learning as prerequisite
    dl_item = next(item for item in res.roadmap if "Deep Learning" in item.skill)
    assert dl_item.priority == "HIGH"
    assert any("Machine Learning" in p for p in dl_item.prerequisites) or dl_item.prerequisite == "Machine Learning"

    # 3. Cloud must be MEDIUM priority
    cloud_item = next(item for item in res.roadmap if "Cloud" in item.skill)
    assert cloud_item.priority == "MEDIUM"

    # Foundational math (Statistics) must be sequenced before advanced neural modeling (Deep Learning)
    stats_idx = skill_names.index(stats_item.skill)
    dl_idx = skill_names.index(dl_item.skill)
    assert stats_idx < dl_idx


# ---------------------------------------------------------------------------
# Test 3: Seeded Course Integrity & 'Demo learning resource' Fallback
# ---------------------------------------------------------------------------

def test_no_fabricated_course_urls_constraint():
    """Verify engine NEVER invents fake course URLs.
    
    Uses only seeded resources. If unseeded, displays 'Demo learning resource'.
    """
    # 1. Seeded skill: Python / Machine Learning (exists in data/courses.json)
    res_seeded = roadmap_generator.generate_roadmap(
        candidate_skills=[],
        target_role="data_scientist",
        missing_skills=["Python", "Machine Learning"]
    )
    
    py_item = next((item for item in res_seeded.roadmap if "Python" in item.skill), None)
    assert py_item is not None
    assert len(py_item.available_learning_resources) > 0
    # Seeded resource has verified URL from freeCodeCamp / MIT OCW
    first_res = py_item.available_learning_resources[0]
    assert first_res.url is not None
    assert any(trusted in first_res.url for trusted in ("freecodecamp.org", "ocw.mit.edu", "coursera.org", "python.org"))

    # 2. Unseeded / arbitrary skill: must return 'Demo learning resource' and NEVER a fake URL
    res_unseeded = roadmap_generator.generate_roadmap(
        candidate_skills=[],
        target_role="backend_engineer",
        missing_skills=["Unseeded Custom Framework"]
    )
    unseeded_item = next(item for item in res_unseeded.roadmap if "Unseeded" in item.skill)
    assert len(unseeded_item.available_learning_resources) > 0
    unseeded_course = unseeded_item.available_learning_resources[0]
    assert "Demo learning resource" in unseeded_course.provider or "Demo learning resource" in unseeded_course.title
    # Must NOT have fabricated web URL
    assert unseeded_course.url in (None, "", "Demo learning resource")


# ---------------------------------------------------------------------------
# Test 4: Dependency-Aware Sequencing (Prerequisites Scheduled First)
# ---------------------------------------------------------------------------

def test_dependency_aware_prerequisite_scheduling():
    """Verify that prerequisites are always sequenced BEFORE dependent frameworks."""
    # Backend Engineer requires: Python, SQL, FastAPI, PostgreSQL, Docker, Git
    # Candidate has empty profile
    res = roadmap_generator.generate_roadmap(
        candidate_skills=[],
        target_role="backend_engineer"
    )

    skill_order = [item.skill for item in res.roadmap]

    # Python must be scheduled BEFORE FastAPI (FastAPI depends on Python)
    py_item = next(item for item in res.roadmap if item.skill_id == "python")
    fastapi_item = next(item for item in res.roadmap if item.skill_id == "fastapi")
    assert py_item.recommended_sequence < fastapi_item.recommended_sequence

    # SQL must be scheduled BEFORE PostgreSQL (PostgreSQL builds on SQL)
    sql_item = next(item for item in res.roadmap if item.skill_id == "sql")
    pg_item = next(item for item in res.roadmap if item.skill_id == "postgresql")
    assert sql_item.recommended_sequence < pg_item.recommended_sequence


# ---------------------------------------------------------------------------
# Test 5: API Endpoint POST /api/v1/recommendations/roadmap
# ---------------------------------------------------------------------------

def test_api_recommendations_roadmap_endpoint():
    """POST /api/v1/recommendations/roadmap with skills list and role."""
    payload = {
        "candidate_skills": ["Python", "SQL"],
        "target_role": "data_scientist",
        "candidate_experience_years": 2.0
    }
    response = client.post("/api/v1/recommendations/roadmap", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "target_role" in data
    assert "total_estimated_weeks" in data
    assert "total_milestones" in data
    assert "roadmap" in data
    assert "prioritized_learning_plan" in data

    assert len(data["roadmap"]) > 0
    first_milestone = data["roadmap"][0]

    # Verify all required roadmap item keys
    assert "skill" in first_milestone
    assert "priority" in first_milestone
    assert "reason" in first_milestone
    assert "prerequisites" in first_milestone
    assert "recommended_sequence" in first_milestone
    assert "estimated_learning_stage" in first_milestone
    assert "available_learning_resources" in first_milestone

    assert first_milestone["recommended_sequence"] == 1
    assert len(first_milestone["available_learning_resources"]) > 0
    first_res = first_milestone["available_learning_resources"][0]
    assert "title" in first_res
    assert "provider" in first_res


def test_api_recommendations_roadmap_with_explicit_gaps():
    """POST /api/v1/recommendations/roadmap with explicit missing_skills and partial_skills."""
    payload = {
        "candidate_skills": ["Python"],
        "target_role": "data_scientist",
        "missing_skills": ["Statistics", "Deep Learning", "Cloud"],
        "partial_skills": ["Data Analysis"]
    }
    response = client.post("/api/v1/recommendations/roadmap", json=payload)
    assert response.status_code == 200

    data = response.json()
    skills_in_plan = [item["skill"] for item in data["roadmap"]]
    assert any("Statistics" in s for s in skills_in_plan)
    assert any("Deep Learning" in s for s in skills_in_plan)
    assert any("Cloud" in s for s in skills_in_plan)
