"""Skill and SkillAlias database repository."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models.skill import Skill, SkillAlias


class SkillRepository:
    @staticmethod
    def create_skill(
        db: Session,
        id: str,
        name: str,
        category: str,
        description: Optional[str] = None,
        importance_weight: float = 1.0,
    ) -> Skill:
        skill = Skill(
            id=id.lower().strip(),
            name=name.strip(),
            category=category.strip(),
            description=description,
            importance_weight=importance_weight,
        )
        db.add(skill)
        db.commit()
        db.refresh(skill)
        return skill

    @staticmethod
    def get_skill(db: Session, skill_id: str) -> Optional[Skill]:
        return db.get(Skill, skill_id.lower().strip())

    @staticmethod
    def get_all_skills(db: Session) -> List[Skill]:
        stmt = select(Skill).order_by(Skill.category, Skill.name)
        return list(db.scalars(stmt).all())

    @staticmethod
    def add_alias(db: Session, skill_id: str, alias: str) -> SkillAlias:
        clean_alias = alias.lower().strip()
        existing = db.scalar(select(SkillAlias).where(SkillAlias.alias == clean_alias))
        if existing:
            return existing

        alias_obj = SkillAlias(alias=clean_alias, skill_id=skill_id)
        db.add(alias_obj)
        db.commit()
        db.refresh(alias_obj)
        return alias_obj

    @staticmethod
    def resolve_alias(db: Session, alias: str) -> Optional[Skill]:
        clean_alias = alias.lower().strip()
        # Direct canonical check
        direct = db.get(Skill, clean_alias)
        if direct:
            return direct
        # Alias lookup
        stmt = select(SkillAlias).where(SkillAlias.alias == clean_alias)
        alias_record = db.scalar(stmt)
        if alias_record:
            return alias_record.skill
        return None


skill_repo = SkillRepository()
