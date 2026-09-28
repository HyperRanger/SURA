import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.database import SessionLocal
from app.services.demo_data import seed_demo_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the fixed Sura backend demo story.")
    parser.add_argument("--reset", action="store_true", help="Replace only the named Sura demo records.")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        with db.begin():
            result = seed_demo_data(db, reset=args.reset)
        print(result)
    finally:
        db.close()


if __name__ == "__main__":
    main()
