"""Skills and Skill Aliases Database Models."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, Float, Integer, ForeignKey, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(
        String(100), primary_key=True
    )  # canonical slug e.g. 'python', 'machine_learning'
    name: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    category: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    importance_weight: Mapped[float] = mapped_column(
        Float, default=1.0, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    aliases: Mapped[List["SkillAlias"]] = relationship(
        "SkillAlias", back_populates="skill", cascade="all, delete-orphan"
    )
    role_associations = relationship(
        "RoleSkill", back_populates="skill", cascade="all, delete-orphan"
    )
    job_associations = relationship(
        "JobSkill", back_populates="skill", cascade="all, delete-orphan"
    )
    courses = relationship(
        "Course", back_populates="skill"
    )

    __table_args__ = (
        Index("idx_skills_category_name", "category", "name"),
    )


class SkillAlias(Base):
    __tablename__ = "skill_aliases"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    alias: Mapped[str] = mapped_column(
        String(150), unique=True, index=True, nullable=False
    )  # e.g. 'py', 'python3', 'cpython'
    skill_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("skills.id", ondelete="CASCADE"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship
    skill: Mapped["Skill"] = relationship(
        "Skill", back_populates="aliases"
    )
