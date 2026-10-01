"""Bank-owned staff and institution settings operations."""

import json
import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.bank.contracts import BANK_PORTAL_ROLES, BANK_STAFF_ROLE_PERMISSIONS
from app.bank.models import BankPartner, BankStaff
from app.bank.service import _audit
from app.models import User
from core.passwords import PasswordTooLong, hash_password


def _staff_or_404(db: Session, bank_id: str, staff_id: str) -> BankStaff:
    staff = db.query(BankStaff).filter(BankStaff.id == staff_id, BankStaff.bank_id == bank_id).one_or_none()
    if staff is None:
        raise HTTPException(status_code=404, detail="Bank staff member not found.")
    return staff


def _serialize_staff(row: BankStaff, user: User | None) -> dict:
    return {
        "staff_id": row.id,
        "user_id": row.user_id,
        "name": user.name if user else None,
        "email": row.email,
        "role": row.role,
        "permissions": json.loads(row.permissions_json),
        "mfa_phone": ("*" * max(0, len(row.mfa_phone or "") - 4) + (row.mfa_phone or "")[-4:]) if row.mfa_phone else None,
        "status": row.status,
        "last_login_at": row.last_login_at.isoformat() if row.last_login_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def list_staff(db: Session, bank_id: str) -> list[dict]:
    rows = db.query(BankStaff).filter(BankStaff.bank_id == bank_id).order_by(BankStaff.created_at.asc(), BankStaff.id.asc()).all()
    users = {user.id: user for user in db.query(User).filter(User.id.in_([row.user_id for row in rows])).all()} if rows else {}
    return [_serialize_staff(row, users.get(row.user_id)) for row in rows]


def create_staff(
    db: Session, bank_id: str, actor_id: str, *, name: str, email: str, role: str,
    mfa_phone: str, temporary_password: str, permissions: list[str] | None = None,
) -> dict:
    if role not in BANK_PORTAL_ROLES:
        raise HTTPException(status_code=400, detail="Unsupported bank staff role.")
    normalized_email = email.strip().lower()
    if db.query(BankStaff.id).filter(BankStaff.email == normalized_email).first() or db.query(User.id).filter(User.phone == normalized_email).first():
        raise HTTPException(status_code=409, detail="A staff account with this email already exists.")
    granted = sorted(set(permissions if permissions is not None else BANK_STAFF_ROLE_PERMISSIONS[role]))
    try:
        password_hash = hash_password(temporary_password)
    except PasswordTooLong as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    user = User(id=f"usr_bank_{uuid.uuid4().hex}", name=name.strip(), phone=normalized_email, role=role, bank_id=bank_id, verified_at=datetime.utcnow(), phone_verified_at=datetime.utcnow())
    staff = BankStaff(id=f"stf_{uuid.uuid4().hex}", bank_id=bank_id, user_id=user.id, email=normalized_email, password_hash=password_hash, role=role, permissions_json=json.dumps(granted), mfa_phone=mfa_phone.strip(), status="active", password_changed_at=datetime.utcnow())
    db.add_all([user, staff])
    _audit(db, bank_id, actor_id, "bank_staff_provisioned", "bank_staff", staff.id, {"role": role})
    db.commit()
    return _serialize_staff(staff, user)


def update_staff(db: Session, bank_id: str, actor_id: str, staff_id: str, *, role: str | None, permissions: list[str] | None, status: str | None) -> dict:
    staff = _staff_or_404(db, bank_id, staff_id)
    if role is not None:
        if role not in BANK_PORTAL_ROLES:
            raise HTTPException(status_code=400, detail="Unsupported bank staff role.")
        staff.role = role
        # BankStaff.user_id has a foreign key to users.id, so this lookup cannot
        # miss in practice; it is checked anyway because a missing row here would
        # raise AttributeError and surface as a 500 on a role change.
        linked_user = db.get(User, staff.user_id)
        if linked_user is None:
            raise HTTPException(status_code=404, detail="Staff account has no linked user.")
        linked_user.role = role
        if permissions is None:
            staff.permissions_json = json.dumps(sorted(BANK_STAFF_ROLE_PERMISSIONS[role]))
    if permissions is not None:
        staff.permissions_json = json.dumps(sorted(set(permissions)))
    if status is not None:
        if status not in {"active", "revoked"}:
            raise HTTPException(status_code=400, detail="Staff status must be active or revoked.")
        staff.status = status
    _audit(db, bank_id, actor_id, "bank_staff_updated", "bank_staff", staff.id, {"role": staff.role, "status": staff.status})
    db.commit()
    return _serialize_staff(staff, db.get(User, staff.user_id))


def get_settings(db: Session, bank_id: str) -> dict:
    bank = db.get(BankPartner, bank_id)
    if bank is None:
        raise HTTPException(status_code=404, detail="Bank not found.")
    return _serialize_settings(bank)


def update_settings(db: Session, bank_id: str, actor_id: str, *, name: str | None, environment: str | None, supported_vendor_categories: list[str] | None, retention_days: int | None, security_settings: dict | None) -> dict:
    bank = db.get(BankPartner, bank_id)
    if bank is None:
        raise HTTPException(status_code=404, detail="Bank not found.")
    if environment is not None:
        if environment not in {"sandbox", "live"}:
            raise HTTPException(status_code=400, detail="Environment must be sandbox or live.")
        bank.environment = environment
    if retention_days is not None:
        if not 30 <= retention_days <= 3650:
            raise HTTPException(status_code=400, detail="Retention must be between 30 and 3650 days.")
        bank.retention_days = retention_days
    if name is not None:
        bank.name = name.strip()
    if supported_vendor_categories is not None:
        bank.supported_vendor_categories_json = json.dumps(sorted(set(supported_vendor_categories)))
    if security_settings is not None:
        bank.security_settings_json = json.dumps(security_settings)
    bank.updated_at = datetime.utcnow()
    _audit(db, bank_id, actor_id, "bank_settings_updated", "bank_partner", bank_id)
    db.commit()
    return _serialize_settings(bank)


def _serialize_settings(bank: BankPartner) -> dict:
    return {
        "bank_id": bank.id,
        "name": bank.name,
        "environment": bank.environment,
        "supported_vendor_categories": json.loads(bank.supported_vendor_categories_json),
        "retention_days": bank.retention_days,
        "security_settings": json.loads(bank.security_settings_json),
        "updated_at": bank.updated_at.isoformat() if bank.updated_at else None,
    }
