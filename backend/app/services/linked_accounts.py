"""Display-only funding-source helpers for the member app.

There is no bank API call here.  ``resolve`` is deterministic demo data and
``link`` stores only a masked reference, never a complete account number.
"""

import hashlib
import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.bank.models import BankAuditEvent, BankPartner
from app.models import LinkedAccount, User


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


def validate_bank(bank_name: str, partner: BankPartner | None = None) -> str:
    candidate = bank_name.strip()
    if candidate not in NIGERIAN_BANKS and (partner is None or candidate != partner.name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Choose a bank from the list.")
    return candidate


def masked_account_number(account_number: str) -> str:
    return f"ending {account_number[-4:]}"


def simulated_display_name(bank_name: str, account_number: str) -> str:
    """Return a repeatable fictional name without retaining the source number."""
    digest = hashlib.sha256(f"{bank_name}:{account_number}".encode("utf-8")).digest()
    return f"{_FIRST_NAMES[digest[0] % len(_FIRST_NAMES)]} {_LAST_NAMES[digest[1] % len(_LAST_NAMES)]}"


def list_banks(db: Session) -> dict[str, object]:
    """Return source-bank labels plus banks that have enabled the Sura API.

    A partner record does not by itself expose a member to that bank. The
    member must still explicitly opt in while linking the source account.
    """
    partners = db.query(BankPartner).order_by(BankPartner.name.asc()).all()
    names = sorted(set(NIGERIAN_BANKS) | {partner.name for partner in partners})
    return {
        "banks": names,
        "sura_supported_banks": [
            {"bank_id": partner.id, "name": partner.name, "environment": partner.environment}
            for partner in partners
        ],
    }


def _partner_or_400(db: Session, partner_bank_id: str | None) -> BankPartner | None:
    if partner_bank_id is None:
        return None
    partner = db.get(BankPartner, partner_bank_id)
    if partner is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Choose a Sura-supported bank from the list.")
    return partner


def resolve_account(db: Session, bank_name: str, account_number: str, partner_bank_id: str | None = None) -> dict[str, str]:
    partner = _partner_or_400(db, partner_bank_id)
    bank = validate_bank(bank_name, partner)
    number = normalise_account_number(account_number)
    return {
        "bank_name": bank,
        "display_name": simulated_display_name(bank, number),
        "account_number_masked": masked_account_number(number),
        "simulated": True,
    }


def link_account(
    db: Session,
    user_id: str,
    bank_name: str,
    account_number: str,
    *,
    partner_bank_id: str | None = None,
    share_with_partner: bool = False,
) -> dict[str, object]:
    """Save a masked label and, only with explicit consent, partner visibility."""
    if share_with_partner and partner_bank_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Choose a Sura-supported bank before sharing data with it.")
    partner = _partner_or_400(db, partner_bank_id)
    resolved = resolve_account(db, bank_name, account_number, partner_bank_id)
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member account not found.")
    now = datetime.utcnow()
    linked = db.query(LinkedAccount).filter(LinkedAccount.user_id == user_id).one_or_none()
    if linked is None:
        linked = LinkedAccount(
            id=str(uuid.uuid4()),
            user_id=user_id,
            **{key: resolved[key] for key in ("bank_name", "display_name", "account_number_masked")},
        )
        db.add(linked)
    else:
        linked.bank_name = resolved["bank_name"]
        linked.display_name = resolved["display_name"]
        linked.account_number_masked = resolved["account_number_masked"]
        linked.created_at = now

    linked.partner_bank_id = partner.id if share_with_partner and partner else None
    linked.shared_with_partner_at = now if linked.partner_bank_id else None
    # ``users.bank_id`` is the existing Bank Portal tenant boundary. It changes
    # only through this explicit member action, never because a bank guesses an
    # account number or sees its name in a drop-down.
    previous_partner_bank_id = user.bank_id
    user.bank_id = linked.partner_bank_id
    if user.bank_id:
        if previous_partner_bank_id != user.bank_id or not user.bank_customer_id:
            user.bank_customer_id = f"SURA-{user.bank_id[-6:].upper()}-{user.id.replace('-', '')[:10].upper()}"
        db.add(BankAuditEvent(
            id=str(uuid.uuid4()),
            bank_id=user.bank_id,
            actor_id=user.id,
            event_type="member_partner_linked",
            subject_type="user",
            subject_id=user.id,
            detail_json='{"simulated": true, "consent": true}',
            occurred_at=now,
        ))
    else:
        user.bank_customer_id = None
    db.commit()
    return serialise(linked)


def get_linked_account(db: Session, user_id: str) -> dict[str, object] | None:
    linked = db.query(LinkedAccount).filter(LinkedAccount.user_id == user_id).one_or_none()
    return serialise(linked) if linked else None


def serialise(linked: LinkedAccount) -> dict[str, object]:
    result: dict[str, object] = {
        "account_id": linked.id,
        "bank_name": linked.bank_name,
        "account_number_masked": linked.account_number_masked,
        "display_name": linked.display_name,
        "created_at": linked.created_at.isoformat(),
        "simulated": True,
    }
    if linked.partner_bank_id:
        result["sura_partner"] = {
            "bank_id": linked.partner_bank_id,
            "shared_at": linked.shared_with_partner_at.isoformat() if linked.shared_with_partner_at else None,
        }
    else:
        result["sura_partner"] = None
    return result
