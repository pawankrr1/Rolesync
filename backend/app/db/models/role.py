"""Career Roles, Role-Skill Mappings, and Career Path Models."""

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


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(
        String(100), primary_key=True
    )  # e.g. 'data_scientist', 'backend_engineer'
    title: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    category: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    typical_experience_years: Mapped[int] = mapped_column(
        Integer, default=2, nullable=False
    )
    market_demand_index: Mapped[float] = mapped_column(
        Float, default=8.0, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    required_skills: Mapped[List["RoleSkill"]] = relationship(
        "RoleSkill", back_populates="role", cascade="all, delete-orphan"
    )
    outgoing_paths = relationship(
        "CareerPath", foreign_keys="CareerPath.source_role_id", back_populates="source_role"
    )
    incoming_paths = relationship(
        "CareerPath", foreign_keys="CareerPath.target_role_id", back_populates="target_role"
    )


class RoleSkill(Base):
    __tablename__ = "role_skills"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    role_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("roles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    skill_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("skills.id", ondelete="CASCADE"), index=True, nullable=False
    )
    importance: Mapped[float] = mapped_column(
        Float, default=1.0, nullable=False
    )
    required_level: Mapped[str] = mapped_column(
        String(50), default="intermediate", nullable=False
    )  # beginner, intermediate, advanced
    is_required: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="required_skills")
    skill = relationship("Skill", back_populates="role_associations")

    __table_args__ = (
        UniqueConstraint("role_id", "skill_id", name="uq_role_skill"),
    )


class CareerPath(Base):
    __tablename__ = "career_paths"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    source_role_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("roles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    target_role_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("roles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    transition_feasibility: Mapped[str] = mapped_column(
        String(100), default="Moderate Bridge Required", nullable=False
    )
    difficulty: Mapped[str] = mapped_column(
        String(50), default="Medium", nullable=False
    )
    rationale: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    source_role = relationship("Role", foreign_keys=[source_role_id], back_populates="outgoing_paths")
    target_role = relationship("Role", foreign_keys=[target_role_id], back_populates="incoming_paths")

    __table_args__ = (
        UniqueConstraint("source_role_id", "target_role_id", name="uq_career_path"),
    )
