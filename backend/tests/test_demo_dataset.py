"""Verification Tests for Deterministic Demo Dataset and Seed Engine.

Acceptance Criteria:
- database can be reset
- seed command works
- seed data is deterministic
- relationships are valid (referential integrity)
- application works entirely offline with seed data
- quota requirements: >= 30 skills, >= 10 roles, >= 50 jobs, >= 20 courses, >= 10 demo candidates
- skill category coverage across all 10 mandated domains
"""

import json
from pathlib import Path
import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.skill import Skill, SkillAlias
from app.db.models.role import Role, RoleSkill, CareerPath
from app.db.models.job import Job, JobSkill
from app.db.models.course import Course
from app.db.models.user import User
from app.db.models.analysis import Analysis, AnalysisSkill
from app.db.seed import seed_database, resolve_data_dir, load_json
from app.core.extractor import SkillExtractor
from app.core.taxonomy import taxonomy


REQUIRED_CATEGORIES = [
    "Programming",
    "Data",
    "AI/ML",
    "Cloud",
    "DevOps",
    "Databases",
    "Web",
    "Cybersecurity",
    "Analytics",
    "Professional skills",
]


def test_seed_files_exist_and_quotas_satisfied():
    """Verify JSON files exist and meet or exceed all mandated quotas."""
    data_dir = resolve_data_dir()
    assert data_dir.exists(), "Data directory must exist"

    skills = load_json(data_dir, "skills.json")
    roles = load_json(data_dir, "roles.json")
    jobs = load_json(data_dir, "jobs.json")
    courses = load_json(data_dir, "courses.json")
    candidates = load_json(data_dir, "demo_candidates.json")

    assert len(skills) >= 30, f"Expected >= 30 skills, got {len(skills)}"
    assert len(roles) >= 10, f"Expected >= 10 roles, got {len(roles)}"
    assert len(jobs) >= 50, f"Expected >= 50 jobs, got {len(jobs)}"
    assert len(courses) >= 20, f"Expected >= 20 courses, got {len(courses)}"
    assert len(candidates) >= 10, f"Expected >= 10 candidates, got {len(candidates)}"


def test_all_mandated_skill_categories_covered():
    """Verify that skills cover all 10 required domains."""
    data_dir = resolve_data_dir()
    skills = load_json(data_dir, "skills.json")
    found_categories = {s["category"] for s in skills}

    for req_cat in REQUIRED_CATEGORIES:
        assert req_cat in found_categories, f"Missing required category: {req_cat}"


def test_no_real_company_claims_and_demo_tagging():
    """Verify jobs do not invent real companies and are clearly tagged as demo data."""
    data_dir = resolve_data_dir()
    jobs = load_json(data_dir, "jobs.json")
    candidates = load_json(data_dir, "demo_candidates.json")

    for j in jobs:
        company = j.get("company", "")
        assert "(Demo)" in company or "Demo" in company, (
            f"Job {j['id']} company '{company}' must be clearly tagged with (Demo)"
        )

    for c in candidates:
        assert c.get("is_demo") is True, f"Candidate {c['id']} must have is_demo=True"
        assert "Sample" in c.get("name", "") or "Demo" in c.get("name", ""), (
            f"Candidate {c['id']} name must clearly indicate sample/demo status"
        )


def test_json_referential_integrity():
    """Verify referential integrity across all JSON seed datasets."""
    data_dir = resolve_data_dir()
    skills = {s["id"]: s for s in load_json(data_dir, "skills.json")}
    roles = {r["id"]: r for r in load_json(data_dir, "roles.json")}
    jobs = load_json(data_dir, "jobs.json")
    courses = load_json(data_dir, "courses.json")
    candidates = load_json(data_dir, "demo_candidates.json")

    # 1. Role skills exist in skills.json
    for r_id, r in roles.items():
        for req in r.get("required_skills", []):
            sk = req["skill_id"]
            assert sk in skills, f"Role {r_id} requires unknown skill '{sk}'"
        for pref in r.get("preferred_skills", []):
            sk = pref["skill_id"]
            assert sk in skills, f"Role {r_id} prefers unknown skill '{sk}'"

    # 2. Job skills exist in skills.json
    for j in jobs:
        for sk in j.get("skills", []):
            assert sk in skills, f"Job {j['id']} references unknown skill '{sk}'"

    # 3. Course skills exist in skills.json
    for c in courses:
        sk = c.get("skill_id")
        if sk:
            assert sk in skills, f"Course {c['id']} references unknown skill '{sk}'"

    # 4. Candidate skills and target roles exist
    for cand in candidates:
        assert cand["target_role_id"] in roles, (
            f"Candidate {cand['id']} targets unknown role '{cand['target_role_id']}'"
        )
        for sk in cand.get("skills", []):
            assert sk in skills, f"Candidate {cand['id']} has unknown skill '{sk}'"


def test_seed_command_and_database_reset(db_session: Session):
    """Verify database reset and deterministic seeding."""
    # First seed run with reset=True
    counts1 = seed_database(db_session, reset=True)
    assert counts1["skills"] >= 30
    assert counts1["roles"] >= 10
    assert counts1["jobs"] >= 50
    assert counts1["courses"] >= 20
    assert counts1["users"] >= 10
    assert counts1["analyses"] >= 10

    # Verify rows in database
    db_skills = db_session.query(Skill).count()
    db_roles = db_session.query(Role).count()
    db_jobs = db_session.query(Job).count()
    db_courses = db_session.query(Course).count()
    db_users = db_session.query(User).count()
    db_analyses = db_session.query(Analysis).count()

    assert db_skills == counts1["skills"]
    assert db_roles == counts1["roles"]
    assert db_jobs == counts1["jobs"]
    assert db_courses == counts1["courses"]
    assert db_users == counts1["users"]
    assert db_analyses == counts1["analyses"]

    # Verify idempotency (second run without reset adds 0 duplicates)
    counts2 = seed_database(db_session, reset=False)
    assert counts2["skills"] == 0
    assert counts2["roles"] == 0
    assert counts2["jobs"] == 0
    assert counts2["courses"] == 0
    assert counts2["users"] == 0

    # Second run with reset=True re-populates exact same counts
    counts3 = seed_database(db_session, reset=True)
    assert counts3["skills"] == counts1["skills"]
    assert counts3["roles"] == counts1["roles"]
    assert counts3["jobs"] == counts1["jobs"]


def test_offline_skill_extraction_on_all_demo_candidates():
    """Verify all 10+ demo candidates can be extracted and matched 100% offline."""
    data_dir = resolve_data_dir()
    candidates = load_json(data_dir, "demo_candidates.json")
    extractor = SkillExtractor()

    for cand in candidates:
        resume_text = cand["resume_text"]
        assert len(resume_text.strip()) > 100, f"Candidate {cand['id']} resume text too short"

        # Offline extraction without external API calls
        report = extractor.extract(resume_text, source="resume")
        assert report.total_skills_detected >= 3, (
            f"Candidate {cand['id']} should yield >= 3 extracted skills offline, got {report.total_skills_detected}"
        )
        assert len(report.categories_found) >= 1

        # Check that extracted skills match known candidate skills
        detected_ids = {s.canonical_id for s in report.skills}
        expected_overlap = set(cand["skills"]).intersection(detected_ids)
        assert len(expected_overlap) >= 2, (
            f"Candidate {cand['id']}: expected overlap between profile skills and extracted skills"
        )


def test_demo_candidate_analyses_in_db(db_session: Session):
    """Verify seeded candidates have valid precomputed match scores and skill breakdowns in DB."""
    seed_database(db_session, reset=True)

    analyses = db_session.query(Analysis).all()
    assert len(analyses) >= 10

    for a in analyses:
        assert 0.0 <= a.match_score <= 100.0
        assert a.score_grade in ["High Alignment", "Moderate Potential", "Needs Upskilling"]
        assert len(a.narrative) > 20

        # Analysis skills
        skills = db_session.query(AnalysisSkill).filter(AnalysisSkill.analysis_id == a.id).all()
        assert len(skills) >= 1
        statuses = {s.match_status for s in skills}
        assert "matched" in statuses
