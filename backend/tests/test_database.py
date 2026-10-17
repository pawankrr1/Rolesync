"""Comprehensive Database Integration & Repository Tests."""

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import SessionLocal, create_all_tables
from app.db.models.user import User
from app.db.models.skill import Skill, SkillAlias
from app.db.models.role import Role, RoleSkill, CareerPath
from app.db.models.job import Job, JobSkill
from app.db.models.course import Course
from app.db.models.analysis import Analysis, AnalysisSkill
from app.db.repositories import (
    skill_repo,
    role_repo,
    job_repo,
    analysis_repo,
    user_repo,
)
from app.db.security import verify_password
from app.db.seed import seed_database




def test_create_and_resolve_skill_and_aliases(db_session: Session):
    # 1. Create canonical skill
    skill_id = "test_rust_lang"
    skill = skill_repo.create_skill(
        db_session,
        id=skill_id,
        name="Rust Programming",
        category="Programming",
        description="Systems language emphasizing memory safety without garbage collection.",
        importance_weight=1.2,
    )
    assert skill.id == skill_id
    assert skill.name == "Rust Programming"
    assert skill.category == "Programming"

    # 2. Add aliases
    alias1 = skill_repo.add_alias(db_session, skill_id, "rust")
    alias2 = skill_repo.add_alias(db_session, skill_id, "rustlang")
    assert alias1.alias == "rust"
    assert alias2.alias == "rustlang"

    # 3. Resolve by alias
    resolved = skill_repo.resolve_alias(db_session, "rust")
    assert resolved is not None
    assert resolved.id == skill_id
    assert resolved.name == "Rust Programming"

    resolved_alt = skill_repo.resolve_alias(db_session, "RUSTLANG")
    assert resolved_alt is not None
    assert resolved_alt.id == skill_id


def test_create_role_and_role_skills(db_session: Session):
    role_id = "test_ai_agent_engineer"
    role = role_repo.create_role(
        db_session,
        id=role_id,
        title="AI Agent Engineer",
        category="Data Science & AI",
        description="Designs autonomous LLM pipelines and multi-agent reasoning systems.",
        typical_experience_years=3,
        market_demand_index=9.8,
    )
    assert role.id == role_id
    assert role.title == "AI Agent Engineer"

    # Add role skill
    # Ensure prerequisite skill exists or create it
    skill = skill_repo.get_skill(db_session, "python")
    if not skill:
        skill = skill_repo.create_skill(db_session, "python", "Python", "Programming")

    role_skill = role_repo.add_role_skill(
        db_session,
        role_id=role_id,
        skill_id="python",
        importance=1.5,
        required_level="advanced",
        is_required=True,
    )
    assert role_skill.role_id == role_id
    assert role_skill.skill_id == "python"
    assert role_skill.required_level == "advanced"
    assert role_skill.is_required is True

    # Check relation navigation
    fetched_role = role_repo.get_role(db_session, role_id)
    assert fetched_role is not None
    assert len(fetched_role.required_skills) >= 1
    assert fetched_role.required_skills[0].skill.name == "Python"


def test_create_career_path(db_session: Session):
    src = "backend_developer"
    tgt = "ml_engineer"
    # Ensure roles exist
    if not role_repo.get_role(db_session, src):
        role_repo.create_role(db_session, src, "Backend Developer", "Web")
    if not role_repo.get_role(db_session, tgt):
        role_repo.create_role(db_session, tgt, "ML Engineer", "AI")

    cp = role_repo.create_career_path(
        db_session,
        source_role_id=src,
        target_role_id=tgt,
        transition_feasibility="Immediate / High Feasibility",
        difficulty="Low",
        rationale="Strong Python & API background makes this a direct natural pivot.",
    )
    assert cp.source_role_id == src
    assert cp.target_role_id == tgt
    assert cp.transition_feasibility == "Immediate / High Feasibility"


def test_create_job_and_job_skills(db_session: Session):
    job = job_repo.create_job(
        db_session,
        title="Senior Python Microservices Architect",
        company="Bharat Cloud Solutions",
        description="Architect resilient microservices using Python and Docker.",
        location="Bengaluru, Karnataka",
        experience_years_min=3,
    )
    assert job.id is not None
    assert job.title == "Senior Python Microservices Architect"

    # Add required skill
    if not skill_repo.get_skill(db_session, "python"):
        skill_repo.create_skill(db_session, "python", "Python", "Programming")

    js = job_repo.add_job_skill(
        db_session,
        job_id=job.id,
        skill_id="python",
        importance=1.4,
        is_required=True,
    )
    assert js.job_id == job.id
    assert js.skill_id == "python"

    fetched_job = job_repo.get_job(db_session, job.id)
    assert fetched_job is not None
    assert len(fetched_job.job_skills) >= 1


def test_user_password_hashing(db_session: Session):
    email = "candidate.pawan@careerintel.dev"
    plain_pw = "SecureHackathonPass2026!"

    user = user_repo.create_user(
        db_session,
        email=email,
        password=plain_pw,
        full_name="Pawan Kumar",
        role="candidate",
    )
    assert user.id is not None
    assert user.email == email
    # Verify password is NOT stored in plaintext
    assert user.hashed_password != plain_pw
    assert user.hashed_password.startswith("$2b$")  # standard bcrypt hash prefix

    # Verify authentication succeeds with valid password
    auth_user = user_repo.authenticate_user(db_session, email, plain_pw)
    assert auth_user is not None
    assert auth_user.id == user.id

    # Verify authentication fails with invalid password
    invalid_auth = user_repo.authenticate_user(db_session, email, "WrongPassword")
    assert invalid_auth is None


def test_analysis_and_analysis_skills(db_session: Session):
    analysis = analysis_repo.create_analysis(
        db_session,
        target_role_title="Data Scientist",
        match_score=82.5,
        score_grade="Exceptional Match",
        narrative="Applicant displays exceptional core requirement alignment across Python and SQL.",
    )
    assert analysis.id is not None
    assert analysis.match_score == 82.5

    # Add matched skill record with sentence evidence
    if not skill_repo.get_skill(db_session, "python"):
        skill_repo.create_skill(db_session, "python", "Python", "Programming")

    skill_item = analysis_repo.add_analysis_skill(
        db_session,
        analysis_id=analysis.id,
        skill_id="python",
        match_status="matched",
        confidence=0.98,
        evidence="Engineered scalable backend data pipelines using Python.",
    )
    assert skill_item.analysis_id == analysis.id
    assert skill_item.match_status == "matched"
    assert skill_item.confidence == 0.98

    # Query analysis with relations
    fetched = analysis_repo.get_analysis(db_session, analysis.id)
    assert fetched is not None
    assert len(fetched.analysis_skills) == 1
    assert fetched.analysis_skills[0].skill_id == "python"


def test_seed_database_quotas(db_session: Session):
    """Verifies that seed data satisfies all required hackathon quotas."""
    seed_database(db_session)

    # 1. At least 20 canonical skills
    all_skills = skill_repo.get_all_skills(db_session)
    assert len(all_skills) >= 20, f"Expected >= 20 skills, got {len(all_skills)}"

    # 2. At least 8 career roles including required roles
    all_roles = role_repo.get_all_roles(db_session)
    assert len(all_roles) >= 8, f"Expected >= 8 roles, got {len(all_roles)}"

    role_titles = {r.title for r in all_roles}
    required_roles = {
        "Data Analyst",
        "Data Scientist",
        "ML Engineer",
        "Software Engineer",
        "Frontend Developer",
        "Backend Developer",
        "DevOps Engineer",
        "Cloud Engineer",
    }
    for req_role in required_roles:
        assert req_role in role_titles, f"Missing required role: {req_role}"

    # 3. At least 30 role-skill relationships
    total_role_skills = db_session.query(RoleSkill).count()
    assert total_role_skills >= 30, f"Expected >= 30 role_skills, got {total_role_skills}"

    # 4. At least 20 jobs
    total_jobs = db_session.query(Job).count()
    assert total_jobs >= 20, f"Expected >= 20 jobs, got {total_jobs}"

    # 5. At least 10 courses
    total_courses = db_session.query(Course).count()
    assert total_courses >= 10, f"Expected >= 10 courses, got {total_courses}"
