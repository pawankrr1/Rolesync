"""Jobs and Job-Skill Requisition Models."""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String,
    Text,
    Float,
    Integer,
    Boolean,
    ForeignKey,
    DateTime,
    func,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(
        String(255), index=True, nullable=False
    )
    company: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    location: Mapped[str] = mapped_column(
        String(255), default="India / Remote", nullable=False
    )
    description: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    experience_years_min: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    job_skills: Mapped[List["JobSkill"]] = relationship(
        "JobSkill", back_populates="job", cascade="all, delete-orphan"
    )
    analyses = relationship(
        "Analysis", back_populates="job"
    )


class JobSkill(Base):
    __tablename__ = "job_skills"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    skill_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("skills.id", ondelete="CASCADE"), index=True, nullable=False
    )
    importance: Mapped[float] = mapped_column(
        Float, default=1.0, nullable=False
    )
    is_required: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="job_skills")
    skill = relationship("Skill", back_populates="job_associations")

    __table_args__ = (
        UniqueConstraint("job_id", "skill_id", name="uq_job_skill"),
    )
