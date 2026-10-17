"""Unit and Integration Tests for Market Intelligence Aggregation Functions.

Validates:
1. Most frequently requested skills aggregation logic and percentage calculation.
2. Skills by role aggregation (required vs preferred split, importance weights).
3. Skills by category aggregation (demand occurrences, category share).
4. Role distribution aggregation (domain mapping, experience bands).
5. Skill-gap trends aggregation (demand % vs candidate supply %, delta calculation).
6. Presence of explicit data source context in every view.
7. Presence of 'Based on the current dataset' notices.
8. Non-implementation of predictive workforce forecasting (predictive_forecasting_active == False).
9. FastAPI endpoints for market intelligence views.
"""

import pytest
from typing import Dict, Any, List
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.market_intelligence import (
    get_most_frequently_requested_skills,
    get_skills_by_role,
    get_skills_by_category,
    get_role_distribution,
    get_skill_gap_trends,
    get_complete_market_intelligence,
    DATASET_NOTICE,
    NO_FORECASTING_NOTICE,
)


# ==============================================================================
# 1. Tests for Most Frequently Requested Skills Aggregation
# ==============================================================================
def test_most_frequently_requested_skills_aggregation():
    """Validates skill ranking, frequency percentage math, and data source context."""
    # Synthetic test fixture
    sample_jobs = [
        {"id": "j1", "skills": ["python", "docker", "sql"]},
        {"id": "j2", "skills": ["python", "docker"]},
        {"id": "j3", "skills": ["python", "fastapi"]},
        {"id": "j4", "skills": ["react"]},
    ]
    sample_skills = [
        {"id": "python", "name": "Python", "category": "Programming", "importance_weight": 1.3},
        {"id": "docker", "name": "Docker", "category": "DevOps", "importance_weight": 1.2},
        {"id": "sql", "name": "SQL", "category": "Programming", "importance_weight": 1.1},
        {"id": "fastapi", "name": "FastAPI", "category": "Web Development", "importance_weight": 1.2},
        {"id": "react", "name": "React", "category": "Web Development", "importance_weight": 1.1},
    ]

    result = get_most_frequently_requested_skills(
        jobs_data=sample_jobs,
        skills_data=sample_skills,
        top_n=3,
    )

    assert result["total_jobs_evaluated"] == 4
    assert len(result["skills"]) == 3
    assert result["data_source_context"].startswith("Seeded Job Requisitions")
    assert DATASET_NOTICE in result["context_note"]

    # Ranked 1: Python (3 out of 4 jobs = 75.0%)
    top_skill = result["skills"][0]
    assert top_skill["skill_id"] == "python"
    assert top_skill["job_count"] == 3
    assert top_skill["frequency_percentage"] == 75.0

    # Ranked 2: Docker (2 out of 4 jobs = 50.0%)
    second_skill = result["skills"][1]
    assert second_skill["skill_id"] == "docker"
    assert second_skill["job_count"] == 2
    assert second_skill["frequency_percentage"] == 50.0


def test_most_frequently_requested_skills_empty():
    """Validates graceful handling of empty job dataset."""
    result = get_most_frequently_requested_skills(jobs_data=[], skills_data=[])
    assert result["total_jobs_evaluated"] == 0
    assert result["skills"] == []
    assert "data_source_context" in result
    assert DATASET_NOTICE in result["context_note"]


# ==============================================================================
# 2. Tests for Skills by Role Aggregation
# ==============================================================================
def test_skills_by_role_aggregation():
    """Validates role-level skill aggregation, required vs preferred splits."""
    sample_roles = [
        {
            "id": "data_scientist",
            "title": "Data Scientist",
            "category": "Data Science & AI",
            "required_skills": [
                {"skill_id": "python", "importance": 1.5, "required_level": "advanced"},
                {"skill_id": "sql", "importance": 1.3, "required_level": "intermediate"},
            ],
            "preferred_skills": [
                {"skill_id": "aws", "importance": 1.0, "required_level": "beginner"},
            ],
        },
        {
            "id": "frontend_dev",
            "title": "Frontend Developer",
            "category": "Web Development",
            "required_skills": [
                {"skill_id": "react", "importance": 1.4, "required_level": "advanced"},
            ],
            "preferred_skills": [],
        },
    ]
    sample_skills = [
        {"id": "python", "name": "Python", "category": "Programming"},
        {"id": "sql", "name": "SQL", "category": "Programming"},
        {"id": "aws", "name": "AWS", "category": "Cloud"},
        {"id": "react", "name": "React", "category": "Web Development"},
    ]

    # Test all roles
    result = get_skills_by_role(roles_data=sample_roles, skills_data=sample_skills)
    assert result["total_roles_evaluated"] == 2
    assert "data_source_context" in result
    assert DATASET_NOTICE in result["context_note"]

    ds_role = result["roles"][0]
    assert ds_role["role_id"] == "data_scientist"
    assert ds_role["required_count"] == 2
    assert ds_role["preferred_count"] == 1
    assert ds_role["total_skills_count"] == 3
    assert ds_role["required_skills"][0]["skill_id"] == "python"
    assert ds_role["required_skills"][0]["is_required"] is True
    assert ds_role["preferred_skills"][0]["skill_id"] == "aws"
    assert ds_role["preferred_skills"][0]["is_required"] is False

    # Test role filtering by specific ID
    filtered_result = get_skills_by_role(
        role_id="frontend_dev",
        roles_data=sample_roles,
        skills_data=sample_skills,
    )
    assert filtered_result["total_roles_evaluated"] == 1
    assert filtered_result["roles"][0]["role_id"] == "frontend_dev"


# ==============================================================================
# 3. Tests for Skills by Category Aggregation
# ==============================================================================
def test_skills_by_category_aggregation():
    """Validates categorization and total demand distribution calculation."""
    sample_skills = [
        {"id": "python", "name": "Python", "category": "Programming"},
        {"id": "sql", "name": "SQL", "category": "Programming"},
        {"id": "docker", "name": "Docker", "category": "DevOps"},
        {"id": "k8s", "name": "Kubernetes", "category": "DevOps"},
    ]
    sample_jobs = [
        {"id": "j1", "skills": ["python", "sql", "docker"]},
        {"id": "j2", "skills": ["docker", "k8s"]},
    ]

    result = get_skills_by_category(skills_data=sample_skills, jobs_data=sample_jobs)
    assert result["total_categories"] >= 2
    assert "data_source_context" in result
    assert DATASET_NOTICE in result["context_note"]

    # Verify occurrence summation:
    # DevOps category (docker=2 + k8s=1 = 3 mentions)
    # Programming category (python=1 + sql=1 = 2 mentions)
    # Total mentions = 5
    cat_by_name = {c["category"]: c for c in result["categories"]}
    assert "Cloud & DevOps" in cat_by_name
    devops_cat = cat_by_name["Cloud & DevOps"]
    assert devops_cat["job_demand_occurrences"] == 3
    assert devops_cat["percentage_of_total_demand"] == 60.0
    assert devops_cat["unique_skills_count"] == 2


# ==============================================================================
# 4. Tests for Role Distribution Aggregation
# ==============================================================================
def test_role_distribution_aggregation():
    """Validates domain representation and experience band categorization."""
    sample_jobs = [
        {"id": "j1", "title": "Senior Machine Learning Engineer", "experience_years_min": 4, "skills": ["python"]},
        {"id": "j2", "title": "Junior Data Analyst", "experience_years_min": 1, "skills": ["sql"]},
        {"id": "j3", "title": "Lead Cloud DevOps Architect", "experience_years_min": 5, "skills": ["docker"]},
        {"id": "j4", "title": "React Frontend Developer", "experience_years_min": 2, "skills": ["react"]},
    ]
    sample_roles = [
        {"id": "ml_eng", "title": "ML Engineer"},
        {"id": "data_analyst", "title": "Data Analyst"},
    ]

    result = get_role_distribution(jobs_data=sample_jobs, roles_data=sample_roles)
    assert result["total_jobs"] == 4
    assert result["total_benchmark_roles"] == 2
    assert "data_source_context" in result
    assert DATASET_NOTICE in result["context_note"]

    # Average min experience: (4 + 1 + 5 + 2) / 4 = 3.0
    assert result["average_minimum_experience_years"] == 3.0

    # Experience band distribution
    bands = {b["experience_band"]: b["job_count"] for b in result["experience_band_distribution"]}
    assert bands["Entry-Level (1-2 years)"] == 2  # j2 (1), j4 (2)
    assert bands["Mid-Level (3-4 years)"] == 1    # j1 (4)
    assert bands["Senior / Lead (5+ years)"] == 1 # j3 (5)

    # Domain distribution sums to total jobs
    domain_sum = sum(d["job_count"] for d in result["domain_distribution"])
    assert domain_sum == 4


# ==============================================================================
# 5. Tests for Skill-Gap Trends Aggregation
# ==============================================================================
def test_skill_gap_trends_aggregation():
    """Validates demand % vs supply %, net gap delta math, and status classifications."""
    # 4 jobs: docker requested in 3 jobs (75%), python in 2 (50%), git in 1 (25%)
    sample_jobs = [
        {"id": "j1", "skills": ["docker", "python"]},
        {"id": "j2", "skills": ["docker", "python"]},
        {"id": "j3", "skills": ["docker", "git"]},
        {"id": "j4", "skills": ["linux"]},
    ]
    # 2 candidates: python in 2 (100%), git in 2 (100%), docker in 0 (0%)
    sample_candidates = [
        {"id": "c1", "skills": ["python", "git"]},
        {"id": "c2", "skills": ["python", "git"]},
    ]
    sample_skills = [
        {"id": "docker", "name": "Docker", "category": "DevOps"},
        {"id": "python", "name": "Python", "category": "Programming"},
        {"id": "git", "name": "Git", "category": "DevOps"},
        {"id": "linux", "name": "Linux", "category": "DevOps"},
    ]

    result = get_skill_gap_trends(
        jobs_data=sample_jobs,
        candidates_data=sample_candidates,
        skills_data=sample_skills,
    )

    assert result["total_jobs_evaluated"] == 4
    assert result["total_candidates_evaluated"] == 2
    assert "data_source_context" in result
    assert DATASET_NOTICE in result["context_note"]

    trends_by_id = {s["skill_id"]: s for s in result["gap_trends"]}

    # Docker: Demand = 3/4 = 75.0%, Supply = 0/2 = 0.0%, Gap Delta = +75.0%
    docker_stat = trends_by_id["docker"]
    assert docker_stat["job_demand_pct"] == 75.0
    assert docker_stat["candidate_supply_pct"] == 0.0
    assert docker_stat["gap_delta_pct"] == 75.0
    assert docker_stat["gap_status"] == "High Unmet Demand"

    # Python: Demand = 2/4 = 50.0%, Supply = 2/2 = 100.0%, Gap Delta = -50.0%
    python_stat = trends_by_id["python"]
    assert python_stat["job_demand_pct"] == 50.0
    assert python_stat["candidate_supply_pct"] == 100.0
    assert python_stat["gap_delta_pct"] == -50.0
    assert python_stat["gap_status"] == "High Candidate Supply"

    # First item in gap_trends is the highest unmet demand
    assert result["gap_trends"][0]["skill_id"] == "docker"


# ==============================================================================
# 6. Master Aggregator and Production Seeded Dataset Validation
# ==============================================================================
def test_complete_market_intelligence_seeded_dataset():
    """Validates complete aggregation over real repository seeded files."""
    data = get_complete_market_intelligence()

    # Metadata assertions
    assert data["metadata"]["total_jobs"] == 50
    assert data["metadata"]["total_roles"] == 11
    assert data["metadata"]["total_skills"] == 58
    assert data["metadata"]["total_candidates"] == 11
    assert data["metadata"]["dataset_notice"] == DATASET_NOTICE
    assert "DEMO & SEEDED DATASET ENVIRONMENT" in data["metadata"]["disclaimer"]
    # Verify predictive workforce forecasting is strictly inactive
    assert data["metadata"]["predictive_forecasting_active"] is False
    assert NO_FORECASTING_NOTICE in data["metadata"]["predictive_forecasting_note"]

    # Section 1: Most Frequently Requested Skills
    freq = data["most_frequently_requested_skills"]
    assert len(freq["skills"]) == 15
    assert freq["total_jobs_evaluated"] == 50
    assert "data_source_context" in freq
    assert freq["skills"][0]["job_count"] >= freq["skills"][-1]["job_count"]

    # Section 2: Skills by Role
    roles = data["skills_by_role"]
    assert roles["total_roles_evaluated"] == 11
    assert "data_source_context" in roles

    # Section 3: Skills by Category
    cats = data["skills_by_category"]
    assert cats["total_categories"] > 0
    assert "data_source_context" in cats

    # Section 4: Role Distribution
    dist = data["role_distribution"]
    assert dist["total_jobs"] == 50
    assert dist["average_minimum_experience_years"] > 0
    assert "data_source_context" in dist

    # Section 5: Skill-Gap Trends
    gaps = data["skill_gap_trends"]
    assert gaps["total_jobs_evaluated"] == 50
    assert gaps["total_candidates_evaluated"] == 11
    assert len(gaps["gap_trends"]) > 0
    assert "data_source_context" in gaps


# ==============================================================================
# 7. FastAPI Endpoint Integration Tests
# ==============================================================================
def test_insights_api_master_endpoint(client: TestClient):
    """Verifies GET /api/v1/insights/market-intelligence HTTP response."""
    response = client.get("/api/v1/insights/market-intelligence")
    assert response.status_code == 200

    payload = response.json()
    assert "metadata" in payload
    assert "most_frequently_requested_skills" in payload
    assert "skills_by_role" in payload
    assert "skills_by_category" in payload
    assert "role_distribution" in payload
    assert "skill_gap_trends" in payload

    # Verify no predictive forecasting
    assert payload["metadata"]["predictive_forecasting_active"] is False

    # Verify each chart section displays data source context
    assert "data_source_context" in payload["most_frequently_requested_skills"]
    assert "data_source_context" in payload["skills_by_role"]
    assert "data_source_context" in payload["skills_by_category"]
    assert "data_source_context" in payload["role_distribution"]
    assert "data_source_context" in payload["skill_gap_trends"]

    # Verify 'Based on the current dataset' exists in responses
    assert DATASET_NOTICE in payload["metadata"]["dataset_notice"]
    assert DATASET_NOTICE in payload["most_frequently_requested_skills"]["context_note"]
    assert DATASET_NOTICE in payload["skills_by_role"]["context_note"]
    assert DATASET_NOTICE in payload["skills_by_category"]["context_note"]
    assert DATASET_NOTICE in payload["role_distribution"]["context_note"]
    assert DATASET_NOTICE in payload["skill_gap_trends"]["context_note"]


def test_insights_api_sub_endpoints(client: TestClient):
    """Verifies individual sub-endpoints for specific views."""
    res1 = client.get("/api/v1/insights/frequently-requested-skills?top_n=5")
    assert res1.status_code == 200
    assert len(res1.json()["skills"]) == 5

    res2 = client.get("/api/v1/insights/skills-by-role?role_id=data_scientist")
    assert res2.status_code == 200
    assert res2.json()["total_roles_evaluated"] == 1

    res3 = client.get("/api/v1/insights/skills-by-category")
    assert res3.status_code == 200
    assert res3.json()["total_categories"] > 0

    res4 = client.get("/api/v1/insights/role-distribution")
    assert res4.status_code == 200
    assert res4.json()["total_jobs"] == 50

    res5 = client.get("/api/v1/insights/skill-gap-trends")
    assert res5.status_code == 200
    assert len(res5.json()["gap_trends"]) > 0
