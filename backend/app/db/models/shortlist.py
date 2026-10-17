"""Candidate Shortlist and Recruiter Engagement Model."""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String,
    Text,
    Float,
    DateTime,
    func,
    Index,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class CandidateShortlist(Base):
    __tablename__ = "candidate_shortlists"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    candidate_id: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False
    )
    candidate_name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    candidate_email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    job_id: Mapped[Optional[str]] = mapped_column(
        String(36), index=True, nullable=True
    )
    job_title: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    match_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default="Shortlisted", nullable=False
    )  # 'Shortlisted', 'Review', 'Interview', 'Rejected'
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_shortlist_cand_job", "candidate_id", "job_id"),
    )
