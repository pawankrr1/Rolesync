#!/usr/bin/env python3
"""Explicit Database Migration Runner for Production & CI/CD.

Executes Alembic migrations forward to 'head', verifies current schema revision,
and provides structured output for container entrypoints.
"""

import sys
import os
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from alembic.config import Config
from alembic import command
from app.config import settings


def run_migrations() -> None:
    """Applies all pending database migrations up to head."""
    print("==================================================================")
    print("📦 EXECUTING DATABASE MIGRATIONS (Alembic -> head)")
    print(f"Target Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    print(f"Environment:     {settings.ENVIRONMENT}")
    print("==================================================================")

    alembic_ini_path = backend_dir / "alembic.ini"
    if not alembic_ini_path.is_file():
        print(f"ERROR: Missing alembic.ini at {alembic_ini_path}", file=sys.stderr)
        sys.exit(1)

    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

    try:
        command.upgrade(alembic_cfg, "head")
        print("✅ Database schema is up to date (revision: head).")
    except Exception as e:
        print(f"❌ Migration failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run_migrations()
