"""Courses and Educational Resources Model."""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String,
    Float,
    Integer,
    Boolean,
    ForeignKey,
    DateTime,
    func,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(
        String(255), index=True, nullable=False
    )
    provider: Mapped[str] = mapped_column(
        String(150), index=True, nullable=False
    )  # e.g. 'MIT OpenCourseWare', 'Coursera', 'freeCodeCamp', 'Official Docs'
    url: Mapped[str] = mapped_column(
        String(500), nullable=False
    )
    skill_id: Mapped[Optional[str]] = mapped_column(
        String(100), ForeignKey("skills.id", ondelete="SET NULL"), index=True, nullable=True
    )
    estimated_hours: Mapped[int] = mapped_column(
        Integer, default=15, nullable=False
    )
    is_free: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    rating: Mapped[float] = mapped_column(
        Float, default=4.8, nullable=False
    )
    course_type: Mapped[str] = mapped_column(
        String(50), default="Online Course", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    skill = relationship("Skill", back_populates="courses")
