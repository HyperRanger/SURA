"""Provision clean, no-activity identities for PWA and Bank Portal testing.

This intentionally does not call the broad demo-data seeder. It creates no
commitments, contributions, vouchers, redemptions, score history, or flags.
Its credentials come only from environment variables and are printed to the
terminal at runtime, never committed to the repository.
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.exc import OperationalError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.bank.contracts import BANK_STAFF_ROLE_PERMISSIONS
from app.bank.models import BankPartner, BankStaff
from app.database import SessionLocal
from app.models import AuthChallenge, Commitment, CommitmentMember, LinkedAccount, SessionRevocation, TrustedDevice, User, Vendor, VendorPayoutAccount, VendorProduct
from core.passwords import hash_password


MEMBER_PASSWORD_ENV = "PWA_TEST_MEMBER_PASSWORD"
VENDOR_PASSWORD_ENV = "PWA_TEST_VENDOR_PASSWORD"
BANK_PASSWORD_ENV = "PWA_TEST_BANK_PASSWORD"

MEMBERS = (
    ("Ayo Adeyemi", "student"), ("Chiamaka Eze", "student"), ("Hauwa Bello", "student"),
    ("Kelechi Obi", "student"), ("Tolu Adebayo", "student"), ("Zainab Musa", "student"),
    ("Bisi Williams", "trader"), ("Emeka Okafor", "trader"), ("Favour Nwosu", "trader"),
    ("Ganiyu Afolabi", "trader"), ("Mfon Akpan", "trader"), ("Tari Briggs", "trader"),
    ("Damilola Grace", "freelancer"), ("Efe Oghene", "freelancer"), ("Ireti James", "freelancer"),
    ("Muna Adebayo", "freelancer"), ("Sadiq Ibrahim", "freelancer"),
    ("Adaeze Ibe", "other"), ("Boma Tamuno", "other"), ("Yejide Adewale", "other"),
)

VENDORS = (
    ("vnd_pwa_test_music", "usr_pwa_vendor_music", "Harmony Demo Music", "music"),
    ("vnd_pwa_test_hardware", "usr_pwa_vendor_hardware", "Buildwell Demo Hardware", "hardware"),
    ("vnd_pwa_test_food", "usr_pwa_vendor_food", "Market Basket Demo", "groceries"),
    ("vnd_pwa_test_fashion", "usr_pwa_vendor_fashion", "Threadline Demo Fashion", "fashion"),
    ("vnd_pwa_test_mobile", "usr_pwa_vendor_mobile", "Pocket Demo Mobile", "mobile"),
    ("vnd_pwa_test_books", "usr_pwa_vendor_books", "Page One Demo Books", "books"),
)

BANKS = (
    ("bnk_pwa_test_orbit", "Orbit Bank", "portal.admin@orbit.demo"),
    ("bnk_pwa_test_lantern", "Lantern Bank", "portal.admin@lantern.demo"),
    ("bnk_pwa_test_river", "River Bank", "portal.admin@river.demo"),
)


def _required_password(name: str) -> str:
    value = os.getenv(name)
    if value is None or len(value) < 12:
        raise SystemExit(f"Set {name} to a demo password of at least 12 characters before running this script.")
    return value


def _member_id(index: int) -> str:
    return f"usr_pwa_test_member_{index:02d}"


def _member_phone(index: int) -> str:
    return f"234809700{index:04d}"


def _member_email(index: int) -> str:
    return f"m{index:02d}@sura.test"


def _has_activity(db, user_ids: list[str]) -> bool:
    return bool(
        db.query(Commitment.id)
        .join(CommitmentMember, CommitmentMember.commitment_id == Commitment.id)
        .filter(CommitmentMember.user_id.in_(user_ids))
        .first()
    )


def _reset(db) -> None:
    member_ids = [_member_id(index) for index in range(1, len(MEMBERS) + 1)]
    vendor_user_ids = [row[1] for row in VENDORS]
    bank_user_ids = [f"usr_{bank_id}_admin" for bank_id, _, _ in BANKS]
    all_user_ids = member_ids + vendor_user_ids + bank_user_ids
    if _has_activity(db, member_ids):
        raise SystemExit("Refusing to reset PWA test identities because one has Lock activity. Remove those test commitments deliberately first.")
    vendor_ids = [row[0] for row in VENDORS]
    bank_ids = [row[0] for row in BANKS]
    db.execute(delete(VendorPayoutAccount).where(VendorPayoutAccount.vendor_id.in_(vendor_ids)))
    db.execute(delete(VendorProduct).where(VendorProduct.vendor_id.in_(vendor_ids)))
    db.execute(delete(LinkedAccount).where(LinkedAccount.user_id.in_(member_ids)))
    db.execute(delete(AuthChallenge).where(AuthChallenge.user_id.in_(all_user_ids)))
    db.execute(delete(TrustedDevice).where(TrustedDevice.user_id.in_(all_user_ids)))
    db.execute(delete(SessionRevocation).where(SessionRevocation.user_id.in_(all_user_ids)))
    db.execute(delete(BankStaff).where(BankStaff.user_id.in_(bank_user_ids)))
    db.execute(delete(User).where(User.id.in_(all_user_ids)))
    db.execute(delete(Vendor).where(Vendor.id.in_(vendor_ids)))
    for bank_id in bank_ids:
        if db.query(User.id).filter(User.bank_id == bank_id).first() is None:
            db.execute(delete(BankPartner).where(BankPartner.id == bank_id))


def seed(db, *, reset: bool) -> dict[str, object]:
    member_password = _required_password(MEMBER_PASSWORD_ENV)
    vendor_password = _required_password(VENDOR_PASSWORD_ENV)
    bank_password = _required_password(BANK_PASSWORD_ENV)
    if reset:
        _reset(db)

    now = datetime.utcnow()
    for index, (name, context) in enumerate(MEMBERS, start=1):
        user_id = _member_id(index)
        user = db.get(User, user_id)
        if user is None:
            db.add(User(
                id=user_id, name=name, phone=_member_phone(index), email=_member_email(index),
                password_hash=hash_password(member_password), role="individual", context=context,
                terms_accepted_at=now, phone_verified_at=now, verified_at=now,
            ))

    for index, (vendor_id, user_id, name, category) in enumerate(VENDORS, start=1):
        vendor = db.get(Vendor, vendor_id)
        if vendor is None:
            vendor = Vendor(id=vendor_id, name=name, category=category, verified_at=now)
            db.add(vendor)
        else:
            vendor.name, vendor.category, vendor.verified_at = name, category, now
        # The vendor login holds a real FK to this merchant. Flush first rather
        # than relying on ORM relationship ordering, because this script uses
        # scalar IDs and Postgres enforces the parent row immediately.
        db.flush()
        user = db.get(User, user_id)
        if user is None:
            db.add(User(
                id=user_id, name=name, phone=f"234809800{index:04d}", email=f"v{index:02d}@sura.test",
                password_hash=hash_password(vendor_password), role="vendor", vendor_id=vendor_id,
                phone_verified_at=now, verified_at=now,
            ))
        for product_number, (product_name, price) in enumerate((("Starter item", 25_000), ("Standard item", 45_000), ("Premium item", 85_000), ("Service package", 18_000), ("Accessories", 12_000)), start=1):
            product_id = f"prd_pwa_test_{index}_{product_number}"
            if db.get(VendorProduct, product_id) is None:
                db.add(VendorProduct(id=product_id, vendor_id=vendor_id, name=product_name, price=price, status="active", created_at=now, updated_at=now))

    for index, (bank_id, name, email) in enumerate(BANKS, start=1):
        bank = db.get(BankPartner, bank_id)
        if bank is None:
            db.add(BankPartner(id=bank_id, name=name, environment="sandbox", created_at=now, updated_at=now))
        user_id = f"usr_{bank_id}_admin"
        user = db.get(User, user_id)
        if user is None:
            db.add(User(id=user_id, name=f"{name} Portal Admin", phone=email, role="bank_admin", bank_id=bank_id, verified_at=now, phone_verified_at=now))
        # SessionLocal deliberately runs without autoflush. Persist the parent
        # rows before creating BankStaff, whose user_id is a real Postgres FK.
        # SQLite's test defaults can hide this ordering issue; Render cannot.
        db.flush()
        staff = db.query(BankStaff).filter(BankStaff.user_id == user_id).one_or_none()
        if staff is None:
            db.add(BankStaff(
                id=f"stf_{bank_id}_admin", bank_id=bank_id, user_id=user_id, email=email,
                password_hash=hash_password(bank_password), role="bank_admin",
                permissions_json=json.dumps(sorted(BANK_STAFF_ROLE_PERMISSIONS["bank_admin"])),
                mfa_phone=f"234809900{index:04d}", status="active", password_changed_at=now, created_at=now,
            ))

    db.commit()
    return {
        "members": [{"name": name, "context": context, "email": _member_email(index), "phone": "0" + _member_phone(index)[3:]} for index, (name, context) in enumerate(MEMBERS, start=1)],
        "vendors": [{"name": name, "category": category, "email": f"v{index:02d}@sura.test", "phone": "0" + f"234809800{index:04d}"[3:]} for index, (_, _, name, category) in enumerate(VENDORS, start=1)],
        "bank_portals": [{"bank": name, "email": email} for _, name, email in BANKS],
        "password_envs": [MEMBER_PASSWORD_ENV, VENDOR_PASSWORD_ENV, BANK_PASSWORD_ENV],
        "note": "No commitments, contributions, vouchers, redemptions, settlement records, or score history were created.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed clean PWA test identities without financial activity.")
    parser.add_argument("--reset", action="store_true", help="Replace only this script's identity fixtures, refusing if they have Lock activity.")
    args = parser.parse_args()
    db = SessionLocal()
    try:
        print(seed(db, reset=args.reset))
        return 0
    except OperationalError as error:
        print("Database connection failed. Use Render's External Database URL when running from your computer.", file=sys.stderr)
        return 2
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
