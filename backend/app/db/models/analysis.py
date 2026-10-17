"""Match Analysis and Analysis-Skill Mapping Models."""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String,
    Text,
    Float,
    Integer,
    ForeignKey,
    DateTime,
    func,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    candidate_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    target_role_id: Mapped[Optional[str]] = mapped_column(
        String(100), ForeignKey("roles.id", ondelete="SET NULL"), index=True, nullable=True
    )
    target_job_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("jobs.id", ondelete="SET NULL"), index=True, nullable=True
    )
    target_role_title: Mapped[str] = mapped_column(
        String(255), index=True, nullable=False
    )
    match_score: Mapped[float] = mapped_column(
        Float, index=True, nullable=False
    )
    score_grade: Mapped[str] = mapped_column(
        String(50), default="High Alignment", nullable=False
    )
    narrative: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    candidate = relationship("User", back_populates="analyses")
    target_role = relationship("Role")
    job = relationship("Job", back_populates="analyses")
    analysis_skills: Mapped[List["AnalysisSkill"]] = relationship(
        "AnalysisSkill", back_populates="analysis", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_analyses_created_score", "created_at", "match_score"),
    )


class AnalysisSkill(Base):
    __tablename__ = "analysis_skills"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("analyses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    skill_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("skills.id", ondelete="CASCADE"), index=True, nullable=False
    )
    match_status: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'matched', 'partial', 'missing'
    confidence: Mapped[float] = mapped_column(
        Float, default=1.0, nullable=False
    )
    evidence: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="analysis_skills")
    skill = relationship("Skill")

    __table_args__ = (
        Index("idx_analysis_skill_status", "analysis_id", "match_status"),
    )
