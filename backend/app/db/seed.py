"""Deterministic Database Seed Script for Career Intelligence.

Populates:
- Canonical Skills & Aliases (from skills.json)
- Benchmark Career Roles & Role-Skill Mappings (from roles.json)
- Strategic Career Paths / Transitions
- Synthetic Job Requisitions across Indian Tech Hubs (from jobs.json)
- Curated Learning Resources (from courses.json)
- Demo Candidate Profiles, Passwords, and Explainable Match Analyses (from demo_candidates.json)

Supports --reset to cleanly wipe and rebuild all tables deterministically.
Works 100% offline without external network or LLM dependencies.
"""

import json
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

# Ensure backend root is in sys.path when executed as standalone script
backend_root = str(Path(__file__).resolve().parent.parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.db.base import Base
from app.db.session import SessionLocal, create_all_tables, reset_database
from app.db.models.user import User
from app.db.models.skill import Skill, SkillAlias
from app.db.models.role import Role, RoleSkill, CareerPath
from app.db.models.job import Job, JobSkill
from app.db.models.course import Course
from app.db.models.analysis import Analysis, AnalysisSkill
from app.db.security import hash_password


def resolve_data_dir(custom_path: Optional[str] = None) -> Path:
    """Finds the directory containing the deterministic JSON seed datasets."""
    candidates = []
    if custom_path:
        candidates.append(Path(custom_path).resolve())

    # Candidate relative paths
    current_file = Path(__file__).resolve()
    # backend/app/db -> repo root / data
    candidates.append(current_file.parent.parent.parent.parent / "data")
    # backend/app/db -> backend / data
    candidates.append(current_file.parent.parent.parent / "data")
    # Current working directory / data
    candidates.append(Path.cwd() / "data")
    # Fallback absolute path
    candidates.append(Path("/Users/pawankumar/Documents/New_assignmnet/Bharat 2.0/data"))

    for p in candidates:
        if p.exists() and (p / "skills.json").is_file():
            return p

    raise FileNotFoundError(
        f"Could not locate seed datasets in any evaluated paths: {[str(p) for p in candidates]}"
    )


def load_json(data_dir: Path, filename: str) -> Any:
    """Loads a JSON file from the target data directory."""
    target_path = data_dir / filename
    if not target_path.exists():
        raise FileNotFoundError(f"Missing required seed file: {target_path}")
    with open(target_path, "r", encoding="utf-8") as f:
        return json.load(f)


def seed_canonical_data(
    db: Session,
    reset: bool = False,
    data_dir: Optional[str] = None
) -> Dict[str, int]:
    """Populates production-grade canonical reference data:
    - Canonical Skills & Skill Aliases (skills.json)
    - Benchmark Career Roles & Role-Skill Mappings (roles.json)
    - Strategic Career Transition Paths (roles.json)
    - Curated Learning Resources / Courses (courses.json)

    Does NOT create any demo users, synthetic candidates, or mock passwords.
    Safe for production bootstrapping.
    """
    data_path = resolve_data_dir(data_dir)
    print(f"[Seed:Canonical] Loading reference datasets from: {data_path}")

    if reset:
        print("[Seed:Canonical] Resetting canonical reference tables...")
        db.query(RoleSkill).delete()
        db.query(CareerPath).delete()
        db.query(Role).delete()
        db.query(Course).delete()
        db.query(SkillAlias).delete()
        db.query(Skill).delete()
        db.commit()

    create_all_tables()

    counts = {
        "skills": 0,
        "skill_aliases": 0,
        "roles": 0,
        "role_skills": 0,
        "career_paths": 0,
        "courses": 0,
    }

    skills_data = load_json(data_path, "skills.json")
    roles_data = load_json(data_path, "roles.json")
    courses_data = load_json(data_path, "courses.json")

    # 1. Skills & Aliases
    skills_by_id: Dict[str, Any] = {}
    for s_item in skills_data:
        s_id = s_item["id"].strip().lower()
        skills_by_id[s_id] = s_item
        existing_skill = db.get(Skill, s_id)
        if not existing_skill:
            skill = Skill(
                id=s_id,
                name=s_item["name"].strip(),
                category=s_item["category"].strip(),
                description=s_item.get("description"),
                importance_weight=float(s_item.get("importance_weight", 1.0)),
            )
            db.add(skill)
            counts["skills"] += 1

        for alias_str in s_item.get("aliases", []):
            clean_alias = alias_str.strip().lower()
            if not clean_alias:
                continue
            existing_alias = db.scalar(
                select(SkillAlias).where(SkillAlias.alias == clean_alias)
            )
            if not existing_alias:
                alias = SkillAlias(alias=clean_alias, skill_id=s_id)
                db.add(alias)
                counts["skill_aliases"] += 1

    db.commit()

    # 2. Roles & Role Skills
    for r_item in roles_data:
        r_id = r_item["id"].strip()
        existing_role = db.get(Role, r_id)
        if not existing_role:
            role = Role(
                id=r_id,
                title=r_item["title"].strip(),
                category=r_item.get("category", "Technology"),
                description=r_item.get("description", ""),
                typical_experience_years=int(r_item.get("typical_experience_years", 2)),
                market_demand_index=float(r_item.get("market_demand_index", 8.0)),
            )
            db.add(role)
            counts["roles"] += 1

        for req in r_item.get("required_skills", []):
            clean_sid = (req.get("skill_id") if isinstance(req, dict) else str(req)).strip().lower()
            importance = float(req.get("importance", 1.2)) if isinstance(req, dict) else 1.2
            required_level = str(req.get("required_level", "intermediate")) if isinstance(req, dict) else "intermediate"
            existing_rs = db.scalar(
                select(RoleSkill).where(
                    RoleSkill.role_id == r_id,
                    RoleSkill.skill_id == clean_sid,
                    RoleSkill.is_required == True,
                )
            )
            if not existing_rs:
                rs = RoleSkill(
                    role_id=r_id,
                    skill_id=clean_sid,
                    importance=importance,
                    required_level=required_level,
                    is_required=True,
                )
                db.add(rs)
                counts["role_skills"] += 1

        for pref in r_item.get("preferred_skills", []):
            clean_sid = (pref.get("skill_id") if isinstance(pref, dict) else str(pref)).strip().lower()
            importance = float(pref.get("importance", 0.8)) if isinstance(pref, dict) else 0.8
            required_level = str(pref.get("required_level", "beginner")) if isinstance(pref, dict) else "beginner"
            existing_rs = db.scalar(
                select(RoleSkill).where(
                    RoleSkill.role_id == r_id,
                    RoleSkill.skill_id == clean_sid,
                    RoleSkill.is_required == False,
                )
            )
            if not existing_rs:
                rs = RoleSkill(
                    role_id=r_id,
                    skill_id=clean_sid,
                    importance=importance,
                    required_level=required_level,
                    is_required=False,
                )
                db.add(rs)
                counts["role_skills"] += 1

    db.commit()

    # 3. Strategic Career Paths
    career_transitions = [
        ("frontend_developer", "fullstack_developer", "High / 85%", "Moderate", "Requires mastering server runtimes (Node.js/Python), REST/GraphQL APIs, and database fundamentals."),
        ("backend_developer", "fullstack_developer", "High / 90%", "Low", "Requires mastering modern frontend SPA frameworks (React/Next.js), CSS systems, and browser state management."),
        ("data_analyst", "data_scientist", "Moderate / 70%", "High", "Requires advancing from descriptive BI/SQL to machine learning modeling, statistical inference, and Python/Pandas workflows."),
        ("backend_developer", "devops_engineer", "High / 80%", "Moderate", "Requires deep immersion in Kubernetes, Terraform, multi-cloud architecture, and automated CI/CD pipelines."),
        ("software_engineer", "backend_developer", "Moderate / 75%", "Moderate", "Requires strengthening system architecture, database indexing, distributed design, and API engineering."),
        ("data_scientist", "ml_engineer", "High / 85%", "Moderate", "Requires transitioning from notebook experimentation to production ML pipelines, model serving, Docker, and MLOps."),
    ]

    for src, tgt, feas, diff, rat in career_transitions:
        src_role = db.get(Role, src)
        tgt_role = db.get(Role, tgt)
        if not src_role or not tgt_role:
            continue
        existing_cp = db.scalar(
            select(CareerPath).where(
                CareerPath.source_role_id == src,
                CareerPath.target_role_id == tgt,
            )
        )
        if not existing_cp:
            cp = CareerPath(
                source_role_id=src,
                target_role_id=tgt,
                transition_feasibility=str(feas),
                difficulty=diff,
                rationale=rat,
            )
            db.add(cp)
            counts["career_paths"] += 1

    db.commit()

    # 4. Curated Courses
    for c_item in courses_data:
        c_id = c_item["id"].strip()
        existing_course = db.get(Course, c_id)
        if not existing_course:
            course = Course(
                id=c_id,
                title=c_item["title"].strip(),
                provider=c_item["provider"].strip(),
                url=c_item["url"].strip(),
                skill_id=c_item.get("skill_id", "").strip().lower() or None,
                estimated_hours=int(c_item.get("estimated_hours", 15)),
                is_free=bool(c_item.get("is_free", True)),
                rating=float(c_item.get("rating", 4.8)),
                course_type=c_item.get("course_type", "Online Course"),
            )
            db.add(course)
            counts["courses"] += 1

    db.commit()
    print("[Seed:Canonical] Reference seeding finished successfully.")
    return counts


def seed_demo_data(
    db: Session,
    reset: bool = False,
    data_dir: Optional[str] = None
) -> Dict[str, int]:
    """Populates development, testing, and demo data:
    - Synthetic Job Requisitions across Indian Tech Hubs (jobs.json)
    - Demo Candidate Profiles, Mock Passwords, and Match Analyses (demo_candidates.json)

    This function should NOT be run in a production environment.
    """
    data_path = resolve_data_dir(data_dir)
    print(f"[Seed:Demo] Loading demo/synthetic datasets from: {data_path}")

    if reset:
        print("[Seed:Demo] Resetting demo candidate and synthetic job records...")
        db.query(AnalysisSkill).delete()
        db.query(Analysis).delete()
        db.query(JobSkill).delete()
        db.query(Job).delete()
        db.query(User).delete()
        db.commit()

    create_all_tables()

    counts = {
        "jobs": 0,
        "job_skills": 0,
        "users": 0,
        "analyses": 0,
        "analysis_skills": 0,
    }

    jobs_data = load_json(data_path, "jobs.json")
    candidates_data = load_json(data_path, "demo_candidates.json")

    # 1. Synthetic Jobs & Job Skills
    for j_item in jobs_data:
        j_id = j_item["id"].strip()
        existing_job = db.get(Job, j_id)
        if not existing_job:
            job = Job(
                id=j_id,
                title=j_item["title"].strip(),
                company=j_item.get("company", "TechCorp Global (Demo)"),
                location=j_item.get("location", "India / Remote"),
                description=j_item.get("description", ""),
                experience_years_min=int(j_item.get("experience_years_min", 1)),
            )
            db.add(job)
            counts["jobs"] += 1

            for s_id in j_item.get("skills", []):
                clean_sid = s_id.strip().lower()
                existing_js = db.scalar(
                    select(JobSkill).where(
                        JobSkill.job_id == j_id,
                        JobSkill.skill_id == clean_sid,
                    )
                )
                if not existing_js:
                    js = JobSkill(
                        job_id=j_id,
                        skill_id=clean_sid,
                        importance=1.2,
                        is_required=True,
                    )
                    db.add(js)
                    counts["job_skills"] += 1

    db.commit()

    # 2. Demo Candidates, Users, & Offline Match Analyses
    default_pw_hash = hash_password("DemoCandidate2026!")

    for cand in candidates_data:
        u_id = cand["id"].strip()
        email = cand["email"].strip().lower()
        existing_user = db.get(User, u_id)
        if not existing_user:
            existing_user = db.scalar(select(User).where(User.email == email))

        if not existing_user:
            user = User(
                id=u_id,
                email=email,
                hashed_password=default_pw_hash,
                full_name=cand["name"].strip(),
                role="candidate",
                is_active=True,
            )
            db.add(user)
            counts["users"] += 1
        else:
            user = existing_user

        target_role = cand.get("target_role_id") or cand.get("target_role", "fullstack_developer")
        analysis_id = f"analysis-{u_id}-{target_role}"
        existing_analysis = db.get(Analysis, analysis_id)
        if not existing_analysis:
            role_rec = db.get(Role, target_role)
            role_title = role_rec.title if role_rec else target_role.replace("_", " ").title()

            req_skills = []
            if role_rec:
                req_skills = [
                    rs
                    for rs in db.scalars(
                        select(RoleSkill.skill_id).where(
                            RoleSkill.role_id == target_role,
                            RoleSkill.is_required == True,
                        )
                    ).all()
                ]

            cand_skills = {str(s).strip().lower(): s for s in cand.get("skills", [])}
            matched_count = sum(1 for s_id in cand_skills if s_id in req_skills)
            total_req = len(req_skills) if req_skills else 1
            calculated_score = round((matched_count / total_req) * 100.0, 1)

            grade = "High Alignment" if calculated_score >= 70 else ("Moderate Potential" if calculated_score >= 45 else "Needs Upskilling")

            analysis = Analysis(
                id=analysis_id,
                candidate_id=u_id,
                target_role_id=target_role,
                target_role_title=role_title,
                match_score=calculated_score,
                score_grade=grade,
                narrative=f"Precomputed match analysis for {cand['name']} targeting {role_title}. Matches {matched_count} of {total_req} core competencies.",
            )
            db.add(analysis)
            counts["analyses"] += 1

            for s_id in cand_skills:
                match_stat = "matched" if s_id in req_skills else "extra"
                askill = AnalysisSkill(
                    analysis_id=analysis_id,
                    skill_id=s_id,
                    match_status=match_stat,
                    confidence=0.92,
                    evidence=f"Demonstrated proficiency in {s_id}.",
                )
                db.add(askill)
                counts["analysis_skills"] += 1

            missing_req = [sid for sid in req_skills if sid not in cand_skills]
            for s_id in missing_req:
                askill = AnalysisSkill(
                    analysis_id=analysis_id,
                    skill_id=s_id,
                    match_status="missing",
                    confidence=0.10,
                    evidence="Required benchmark skill not detected in candidate profile.",
                )
                db.add(askill)
                counts["analysis_skills"] += 1

    db.commit()
    print("[Seed:Demo] Demo seeding finished successfully.")
    return counts


def seed_database(
    db: Session,
    reset: bool = False,
    data_dir: Optional[str] = None,
    include_demo_data: bool = True
) -> Dict[str, int]:
    """Deterministically populates the database using curated seed datasets.
    
    Args:
        db: Active SQLAlchemy Session
        reset: If True, completely resets (wipes) all tables before seeding
        data_dir: Optional path to directory containing seed JSON files
        include_demo_data: If True, populates synthetic jobs and demo candidates.
                           If False, populates canonical reference data only.
    
    Returns:
        Dictionary of seeded record counts by entity type
    """
    data_path = resolve_data_dir(data_dir)
    print(f"[Seed] Initializing seed routine from: {data_path} (include_demo_data={include_demo_data})")

    if reset:
        print("[Seed] Resetting database tables in safe dependency order...")
        db.query(AnalysisSkill).delete()
        db.query(Analysis).delete()
        db.query(JobSkill).delete()
        db.query(Job).delete()
        db.query(RoleSkill).delete()
        db.query(CareerPath).delete()
        db.query(Role).delete()
        db.query(Course).delete()
        db.query(SkillAlias).delete()
        db.query(Skill).delete()
        db.query(User).delete()
        db.commit()

    canonical_counts = seed_canonical_data(db, reset=False, data_dir=data_dir)

    demo_counts = {
        "jobs": 0,
        "job_skills": 0,
        "users": 0,
        "analyses": 0,
        "analysis_skills": 0,
    }

    if include_demo_data:
        demo_counts = seed_demo_data(db, reset=False, data_dir=data_dir)

    total_counts = {**canonical_counts, **demo_counts}
    print("[Seed] Seeding completed with record summary:")
    for k, v in total_counts.items():
        print(f"  - {k:<18}: {v} records")

    return total_counts

def main():
    """CLI Entry point for database seeding."""
    parser = argparse.ArgumentParser(
        description="Career Intelligence Deterministic Seed Script."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Wipe and recreate database before seeding",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Custom path to directory containing seed JSON files",
    )
    parser.add_argument(
        "--canonical-only",
        action="store_true",
        help="Seed canonical reference data only (skills, roles, courses) - recommended for production",
    )
    parser.add_argument(
        "--demo-only",
        action="store_true",
        help="Seed demo candidates and synthetic jobs only",
    )
    args = parser.parse_args()

    session = SessionLocal()
    try:
        if args.canonical_only:
            results = seed_canonical_data(
                db=session,
                reset=args.reset,
                data_dir=args.data_dir,
            )
            print("\nSUCCESS: Canonical reference data seeded successfully.")
        elif args.demo_only:
            results = seed_demo_data(
                db=session,
                reset=args.reset,
                data_dir=args.data_dir,
            )
            print("\nSUCCESS: Demo data seeded successfully.")
        else:
            results = seed_database(
                db=session,
                reset=args.reset,
                data_dir=args.data_dir,
                include_demo_data=True,
            )
            print("\nSUCCESS: Database seeded deterministically.")
    except Exception as e:
        print(f"\nERROR seeding database: {e}", file=sys.stderr)
        session.rollback()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
