"""Seed the public demo catalogue without creating or deleting user accounts."""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.database import SessionLocal
from app.services.demo_data import seed_demo_catalogue


def main() -> int:
    db = SessionLocal()
    try:
        with db.begin():
            print(seed_demo_catalogue(db))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
