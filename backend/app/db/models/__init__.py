"""Export all database models."""

from app.db.models.user import User
from app.db.models.skill import Skill, SkillAlias
from app.db.models.role import Role, RoleSkill, CareerPath
from app.db.models.job import Job, JobSkill
from app.db.models.course import Course
from app.db.models.analysis import Analysis, AnalysisSkill
from app.db.models.shortlist import CandidateShortlist

__all__ = [
    "User",
    "Skill",
    "SkillAlias",
    "Role",
    "RoleSkill",
    "CareerPath",
    "Job",
    "JobSkill",
    "Course",
    "Analysis",
    "AnalysisSkill",
    "CandidateShortlist",
]
