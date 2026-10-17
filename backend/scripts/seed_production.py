#!/usr/bin/env python3
"""Production Database Seed Script.

Seeds ONLY canonical reference data:
- Canonical Skill Taxonomy & Aliases (skills.json)
- Standard Career Roles & Requirements (roles.json)
- Strategic Career Paths (roles.json)
- Curated Learning Courses & Roadmaps (courses.json)

GUARANTEE:
Never seeds demo users, mock candidate profiles, or synthetic job postings.
Safe for production initialization.
"""

import sys
import os
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal
from app.db.seed import seed_canonical_data
from app.config import settings


def run_production_seed() -> None:
    print("==================================================================")
    print("🌱 EXECUTING PRODUCTION CANONICAL SEED")
    print(f"Target Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    print(f"Environment:     {settings.ENVIRONMENT}")
    print("Zero-Demo-Data Guarantee: Active (Canonical Reference Data Only)")
    print("==================================================================")

    session = SessionLocal()
    try:
        counts = seed_canonical_data(db=session, reset=False)
        print("✅ Canonical reference seeding completed successfully:")
        for entity, count in counts.items():
            print(f"   • {entity:<16}: {count} records verified")
    except Exception as e:
        print(f"❌ Production seed failed: {e}", file=sys.stderr)
        session.rollback()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    run_production_seed()
