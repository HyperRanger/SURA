"""Display-only funding-source helpers for the member app.

There is no bank API call here.  ``resolve`` is deterministic demo data and
``link`` stores only a masked reference, never a complete account number.
"""

import hashlib
import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import LinkedAccount


NIGERIAN_BANKS = (
    "Access Bank",
    "Citibank Nigeria",
    "Ecobank Nigeria",
    "Fidelity Bank",
    "FirstBank",
    "FCMB",
    "GTBank",
    "Jaiz Bank",
    "Kuda",
    "Moniepoint MFB",
    "Opay",
    "PalmPay",
    "Polaris Bank",
    "Stanbic IBTC Bank",
    "Sterling Bank",
    "UBA",
    "Union Bank",
    "Wema Bank",
    "Zenith Bank",
)

# A small, intentionally fictional name pool.  It helps the simulated lookup
# read naturally on screen without impersonating a real account-holder lookup.
_FIRST_NAMES = ("Amina", "Chiamaka", "Damilola", "Ifeanyi", "Kelechi", "Teni", "Tunde", "Zainab")
_LAST_NAMES = ("Adeyemi", "Bello", "Eze", "Ibrahim", "Okafor", "Olawale", "Uche", "Yakubu")


def normalise_account_number(account_number: str) -> str:
    digits = "".join(character for character in account_number if character.isdigit())
    if len(digits) != 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter a 10-digit Nigerian account number.",
        )
    return digits


def validate_bank(bank_name: str) -> str:
    candidate = bank_name.strip()
    if candidate not in NIGERIAN_BANKS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Choose a bank from the list.")
    return candidate


def masked_account_number(account_number: str) -> str:
    return f"ending {account_number[-4:]}"


def simulated_display_name(bank_name: str, account_number: str) -> str:
    """Return a repeatable fictional name without retaining the source number."""
    digest = hashlib.sha256(f"{bank_name}:{account_number}".encode("utf-8")).digest()
    return f"{_FIRST_NAMES[digest[0] % len(_FIRST_NAMES)]} {_LAST_NAMES[digest[1] % len(_LAST_NAMES)]}"


def list_banks() -> dict[str, list[str]]:
    return {"banks": list(NIGERIAN_BANKS)}


def resolve_account(bank_name: str, account_number: str) -> dict[str, str]:
    bank = validate_bank(bank_name)
    number = normalise_account_number(account_number)
    return {
        "bank_name": bank,
        "display_name": simulated_display_name(bank, number),
        "account_number_masked": masked_account_number(number),
        "simulated": True,
    }


def link_account(db: Session, user_id: str, bank_name: str, account_number: str) -> dict[str, str]:
    resolved = resolve_account(bank_name, account_number)
    linked = db.query(LinkedAccount).filter(LinkedAccount.user_id == user_id).one_or_none()
    if linked is None:
        linked = LinkedAccount(id=str(uuid.uuid4()), user_id=user_id, **{key: resolved[key] for key in ("bank_name", "display_name", "account_number_masked")})
        db.add(linked)
    else:
        linked.bank_name = resolved["bank_name"]
        linked.display_name = resolved["display_name"]
        linked.account_number_masked = resolved["account_number_masked"]
        linked.created_at = datetime.utcnow()
    db.commit()
    return serialise(linked)


def get_linked_account(db: Session, user_id: str) -> dict[str, str] | None:
    linked = db.query(LinkedAccount).filter(LinkedAccount.user_id == user_id).one_or_none()
    return serialise(linked) if linked else None


def serialise(linked: LinkedAccount) -> dict[str, str]:
    return {
        "account_id": linked.id,
        "bank_name": linked.bank_name,
        "account_number_masked": linked.account_number_masked,
        "display_name": linked.display_name,
        "created_at": linked.created_at.isoformat(),
        "simulated": True,
    }
