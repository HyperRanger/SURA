import argparse
import sys
from pathlib import Path

from sqlalchemy.exc import OperationalError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.database import SessionLocal
from app.services.demo_data import seed_demo_data
from core.config import get_settings


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed the fixed Sura backend demo story.")
    parser.add_argument("--reset", action="store_true", help="Replace only the named Sura demo records.")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        with db.begin():
            result = seed_demo_data(db, reset=args.reset)
        print(result)
        return 0
    except OperationalError as error:
        # Render's internal host has no public DNS record. A developer running
        # this command from Windows or another external machine needs the
        # External Database URL, while a Render web service needs the Internal
        # Database URL. Keep the URL itself out of the error output because it
        # can contain a password.
        if "getaddrinfo failed" in str(error):
            host = get_settings().database_url.split("@")[-1].split("/")[0]
            print(
                "Cannot resolve the configured database host "
                f"({host}). If this is a Render internal hostname, run this "
                "command inside Render or set local DATABASE_URL to Render's "
                "External Database URL (with sslmode=require).",
                file=sys.stderr,
            )
            return 2
        raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
