"""Masked vendor settlement-account labels for the simulated MVP."""

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import VendorPayoutAccount
from app.services import linked_accounts


def get_payout_account(db: Session, vendor_id: str) -> dict[str, object] | None:
    row = db.query(VendorPayoutAccount).filter(VendorPayoutAccount.vendor_id == vendor_id).one_or_none()
    return _serialise(row) if row else None


def save_payout_account(db: Session, vendor_id: str, bank_name: str, account_number: str) -> dict[str, object]:
    resolved = linked_accounts.resolve_account(db, bank_name, account_number)
    row = db.query(VendorPayoutAccount).filter(VendorPayoutAccount.vendor_id == vendor_id).one_or_none()
    now = datetime.utcnow()
    if row is None:
        row = VendorPayoutAccount(
            id=str(uuid.uuid4()),
            vendor_id=vendor_id,
            bank_name=resolved["bank_name"],
            account_number_masked=resolved["account_number_masked"],
            display_name=resolved["display_name"],
            created_at=now,
            updated_at=now,
        )
        db.add(row)
    else:
        row.bank_name = resolved["bank_name"]
        row.account_number_masked = resolved["account_number_masked"]
        row.display_name = resolved["display_name"]
        row.updated_at = now
    db.commit()
    return _serialise(row)


def _serialise(row: VendorPayoutAccount) -> dict[str, object]:
    return {
        "payout_account_id": row.id,
        "bank_name": row.bank_name,
        "account_number_masked": row.account_number_masked,
        "display_name": row.display_name,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
        "simulated": True,
    }
