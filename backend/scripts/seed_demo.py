#!/usr/bin/env python3
"""Demo / Development Database Seed Script.

Seeds:
- Synthetic Job Requisitions across Indian Tech Hubs (jobs.json)
- Demo Candidate Profiles, Mock Passwords, and Match Analyses (demo_candidates.json)

CAUTION:
Intended exclusively for development, demo, and staging environments.
Do NOT run against a production database.
"""

import sys
import os
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal
from app.db.seed import seed_demo_data
from app.config import settings


def run_demo_seed() -> None:
    print("==================================================================")
    print("🧪 EXECUTING DEMO & DEVELOPMENT SEED")
    print(f"Target Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    print(f"Environment:     {settings.ENVIRONMENT}")
    print("==================================================================")

    if settings.is_production:
        print("⚠️  WARNING: Running demo seed in a PRODUCTION environment is restricted.")
        confirm = os.environ.get("CONFIRM_PRODUCTION_DEMO_SEED", "").lower()
        if confirm != "true":
            print("❌ Aborted. Set CONFIRM_PRODUCTION_DEMO_SEED=true to force demo seeding in production.", file=sys.stderr)
            sys.exit(1)

    session = SessionLocal()
    try:
        counts = seed_demo_data(db=session, reset=False)
        print("✅ Demo seeding completed successfully:")
        for entity, count in counts.items():
            print(f"   • {entity:<16}: {count} records verified")
    except Exception as e:
        print(f"❌ Demo seed failed: {e}", file=sys.stderr)
        session.rollback()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    run_demo_seed()
