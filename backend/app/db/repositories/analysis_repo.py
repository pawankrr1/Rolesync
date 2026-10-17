"""Analysis and AnalysisSkill repository."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models.analysis import Analysis, AnalysisSkill


class AnalysisRepository:
    @staticmethod
    def create_analysis(
        db: Session,
        target_role_title: str,
        match_score: float,
        score_grade: str,
        candidate_id: Optional[str] = None,
        target_role_id: Optional[str] = None,
        target_job_id: Optional[str] = None,
        narrative: Optional[str] = None,
    ) -> Analysis:
        analysis = Analysis(
            target_role_title=target_role_title,
            match_score=match_score,
            score_grade=score_grade,
            candidate_id=candidate_id,
            target_role_id=target_role_id,
            target_job_id=target_job_id,
            narrative=narrative,
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis

    @staticmethod
    def add_analysis_skill(
        db: Session,
        analysis_id: str,
        skill_id: str,
        match_status: str,
        confidence: float = 1.0,
        evidence: Optional[str] = None,
    ) -> AnalysisSkill:
        item = AnalysisSkill(
            analysis_id=analysis_id,
            skill_id=skill_id,
            match_status=match_status,
            confidence=confidence,
            evidence=evidence,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def get_analysis(db: Session, analysis_id: str) -> Optional[Analysis]:
        return db.get(Analysis, analysis_id)

    @staticmethod
    def get_candidate_analyses(
        db: Session, candidate_id: str, limit: int = 20
    ) -> List[Analysis]:
        stmt = (
            select(Analysis)
            .where(Analysis.candidate_id == candidate_id)
            .order_by(Analysis.created_at.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt).all())


analysis_repo = AnalysisRepository()
