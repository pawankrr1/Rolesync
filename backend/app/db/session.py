"""Database Engine & Session Management."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings

# Engine configuration with dialect-specific options
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables() -> None:
    """Create all registered database tables."""
    from app.db.base import Base
    import app.db.models  # Ensure all models are imported before creating tables
    Base.metadata.create_all(bind=engine)


def drop_all_tables() -> None:
    """Drop all registered database tables."""
    from app.db.base import Base
    import app.db.models
    Base.metadata.drop_all(bind=engine)


def reset_database() -> None:
    """Drop and recreate all database tables."""
    drop_all_tables()
    create_all_tables()
