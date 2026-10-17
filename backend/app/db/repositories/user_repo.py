"""User repository with secure password hashing."""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models.user import User
from app.db.security import hash_password, verify_password


class UserRepository:
    @staticmethod
    def create_user(
        db: Session,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        role: str = "candidate",
    ) -> User:
        clean_email = email.lower().strip()
        existing = db.scalar(select(User).where(User.email == clean_email))
        if existing:
            raise ValueError(f"User with email '{clean_email}' already exists.")

        user = User(
            email=clean_email,
            hashed_password=hash_password(password),
            full_name=full_name.strip() if full_name else None,
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        return db.scalar(select(User).where(User.email == email.lower().strip()))

    @staticmethod
    def authenticate_user(
        db: Session, email: str, password: str
    ) -> Optional[User]:
        user = UserRepository.get_user_by_email(db, email)
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


user_repo = UserRepository()
