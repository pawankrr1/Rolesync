"""Job and JobSkill repository."""

from typing import List, Optional
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from app.db.models.job import Job, JobSkill


class JobRepository:
    @staticmethod
    def create_job(
        db: Session,
        title: str,
        description: str,
        company: Optional[str] = None,
        location: str = "India / Remote",
        experience_years_min: int = 1,
    ) -> Job:
        job = Job(
            title=title.strip(),
            company=company.strip() if company else None,
            description=description.strip(),
            location=location.strip(),
            experience_years_min=experience_years_min,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_job(db: Session, job_id: str) -> Optional[Job]:
        stmt = select(Job).options(selectinload(Job.job_skills)).where(Job.id == job_id)
        return db.scalar(stmt)

    @staticmethod
    def get_all_jobs(db: Session, limit: int = 50, offset: int = 0) -> List[Job]:
        stmt = select(Job).options(selectinload(Job.job_skills)).order_by(Job.created_at.desc()).limit(limit).offset(offset)
        return list(db.scalars(stmt).all())

    @staticmethod
    def add_job_skill(
        db: Session,
        job_id: str,
        skill_id: str,
        importance: float = 1.0,
        is_required: bool = True,
    ) -> JobSkill:
        stmt = select(JobSkill).where(
            JobSkill.job_id == job_id, JobSkill.skill_id == skill_id
        )
        existing = db.scalar(stmt)
        if existing:
            existing.importance = importance
            existing.is_required = is_required
            db.commit()
            db.refresh(existing)
            return existing

        js = JobSkill(
            job_id=job_id,
            skill_id=skill_id,
            importance=importance,
            is_required=is_required,
        )
        db.add(js)
        db.commit()
        db.refresh(js)
        return js

    @staticmethod
    def update_job(
        db: Session,
        job_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        company: Optional[str] = None,
        location: Optional[str] = None,
        experience_years_min: Optional[int] = None,
    ) -> Optional[Job]:
        job = db.get(Job, job_id)
        if not job:
            return None
        if title is not None:
            job.title = title.strip()
        if description is not None:
            job.description = description.strip()
        if company is not None:
            job.company = company.strip() if company else None
        if location is not None:
            job.location = location.strip()
        if experience_years_min is not None:
            job.experience_years_min = experience_years_min
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def delete_job(db: Session, job_id: str) -> bool:
        job = db.get(Job, job_id)
        if not job:
            return False
        db.delete(job)
        db.commit()
        return True

    @staticmethod
    def replace_job_skills(
        db: Session,
        job_id: str,
        required_skills: List[str],
        preferred_skills: List[str],
    ) -> None:
        # Delete existing skills
        from sqlalchemy import delete
        db.execute(delete(JobSkill).where(JobSkill.job_id == job_id))
        
        # Insert required skills
        for s in required_skills:
            clean_s = s.strip()
            if clean_s:
                db.add(JobSkill(
                    job_id=job_id,
                    skill_id=clean_s.lower().replace(" ", "_"),
                    importance=1.5,
                    is_required=True
                ))
        
        # Insert preferred skills
        for s in preferred_skills:
            clean_s = s.strip()
            if clean_s:
                db.add(JobSkill(
                    job_id=job_id,
                    skill_id=clean_s.lower().replace(" ", "_"),
                    importance=1.0,
                    is_required=False
                ))
        db.commit()


job_repo = JobRepository()
