"""Candidate Shortlist repository."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, delete
from app.db.models.shortlist import CandidateShortlist


class ShortlistRepository:
    @staticmethod
    def add_or_update(
        db: Session,
        candidate_id: str,
        candidate_name: str,
        candidate_email: Optional[str] = None,
        job_id: Optional[str] = None,
        job_title: Optional[str] = None,
        match_score: Optional[float] = None,
        status: str = "Shortlisted",
        notes: Optional[str] = None,
    ) -> CandidateShortlist:
        stmt = select(CandidateShortlist).where(
            CandidateShortlist.candidate_id == candidate_id,
            CandidateShortlist.job_id == job_id,
        )
        existing = db.scalar(stmt)
        if existing:
            existing.candidate_name = candidate_name
            if candidate_email:
                existing.candidate_email = candidate_email
            if job_title:
                existing.job_title = job_title
            if match_score is not None:
                existing.match_score = match_score
            existing.status = status
            if notes is not None:
                existing.notes = notes
            db.commit()
            db.refresh(existing)
            return existing

        item = CandidateShortlist(
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            job_id=job_id,
            job_title=job_title,
            match_score=match_score,
            status=status,
            notes=notes,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def remove(
        db: Session,
        candidate_id: str,
        job_id: Optional[str] = None,
    ) -> bool:
        if job_id:
            stmt = delete(CandidateShortlist).where(
                CandidateShortlist.candidate_id == candidate_id,
                CandidateShortlist.job_id == job_id,
            )
        else:
            stmt = delete(CandidateShortlist).where(
                CandidateShortlist.candidate_id == candidate_id,
            )
        result = db.execute(stmt)
        db.commit()
        return result.rowcount > 0

    @staticmethod
    def get_all(
        db: Session,
        job_id: Optional[str] = None,
    ) -> List[CandidateShortlist]:
        query = select(CandidateShortlist)
        if job_id:
            query = query.where(CandidateShortlist.job_id == job_id)
        query = query.order_by(CandidateShortlist.created_at.desc())
        return list(db.scalars(query).all())

    @staticmethod
    def is_shortlisted(
        db: Session,
        candidate_id: str,
        job_id: Optional[str] = None,
    ) -> bool:
        if job_id:
            stmt = select(CandidateShortlist).where(
                CandidateShortlist.candidate_id == candidate_id,
                CandidateShortlist.job_id == job_id,
            )
        else:
            stmt = select(CandidateShortlist).where(
                CandidateShortlist.candidate_id == candidate_id,
            )
        return db.scalar(stmt) is not None

    @staticmethod
    def update_status(
        db: Session,
        shortlist_id: str,
        status: str,
        notes: Optional[str] = None,
    ) -> Optional[CandidateShortlist]:
        item = db.get(CandidateShortlist, shortlist_id)
        if not item:
            return None
        item.status = status
        if notes is not None:
            item.notes = notes
        db.commit()
        db.refresh(item)
        return item


shortlist_repo = ShortlistRepository()
