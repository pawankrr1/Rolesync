"""Role, RoleSkill, and CareerPath repository."""

from typing import List, Optional
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from app.db.models.role import Role, RoleSkill, CareerPath


class RoleRepository:
    @staticmethod
    def create_role(
        db: Session,
        id: str,
        title: str,
        category: str,
        description: Optional[str] = None,
        typical_experience_years: int = 2,
        market_demand_index: float = 8.0,
    ) -> Role:
        role = Role(
            id=id.strip(),
            title=title.strip(),
            category=category.strip(),
            description=description,
            typical_experience_years=typical_experience_years,
            market_demand_index=market_demand_index,
        )
        db.add(role)
        db.commit()
        db.refresh(role)
        return role

    @staticmethod
    def get_role(db: Session, role_id: str) -> Optional[Role]:
        stmt = select(Role).options(selectinload(Role.required_skills)).where(Role.id == role_id.strip())
        return db.scalar(stmt)

    @staticmethod
    def get_all_roles(db: Session) -> List[Role]:
        stmt = select(Role).options(selectinload(Role.required_skills)).order_by(Role.title)
        return list(db.scalars(stmt).all())

    @staticmethod
    def add_role_skill(
        db: Session,
        role_id: str,
        skill_id: str,
        importance: float = 1.0,
        required_level: str = "intermediate",
        is_required: bool = True,
    ) -> RoleSkill:
        stmt = select(RoleSkill).where(
            RoleSkill.role_id == role_id, RoleSkill.skill_id == skill_id
        )
        existing = db.scalar(stmt)
        if existing:
            existing.importance = importance
            existing.required_level = required_level
            existing.is_required = is_required
            db.commit()
            db.refresh(existing)
            return existing

        rs = RoleSkill(
            role_id=role_id,
            skill_id=skill_id,
            importance=importance,
            required_level=required_level,
            is_required=is_required,
        )
        db.add(rs)
        db.commit()
        db.refresh(rs)
        return rs

    @staticmethod
    def create_career_path(
        db: Session,
        source_role_id: str,
        target_role_id: str,
        transition_feasibility: str = "Moderate Bridge Required",
        difficulty: str = "Medium",
        rationale: Optional[str] = None,
    ) -> CareerPath:
        stmt = select(CareerPath).where(
            CareerPath.source_role_id == source_role_id,
            CareerPath.target_role_id == target_role_id,
        )
        existing = db.scalar(stmt)
        if existing:
            return existing

        cp = CareerPath(
            source_role_id=source_role_id,
            target_role_id=target_role_id,
            transition_feasibility=transition_feasibility,
            difficulty=difficulty,
            rationale=rationale,
        )
        db.add(cp)
        db.commit()
        db.refresh(cp)
        return cp


role_repo = RoleRepository()
