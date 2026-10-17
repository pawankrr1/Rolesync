"""Database repositories export."""

from app.db.repositories.skill_repo import skill_repo, SkillRepository
from app.db.repositories.role_repo import role_repo, RoleRepository
from app.db.repositories.job_repo import job_repo, JobRepository
from app.db.repositories.analysis_repo import analysis_repo, AnalysisRepository
from app.db.repositories.user_repo import user_repo, UserRepository
from app.db.repositories.shortlist_repo import shortlist_repo, ShortlistRepository

__all__ = [
    "skill_repo",
    "SkillRepository",
    "role_repo",
    "RoleRepository",
    "job_repo",
    "JobRepository",
    "analysis_repo",
    "AnalysisRepository",
    "user_repo",
    "UserRepository",
    "shortlist_repo",
    "ShortlistRepository",
]
