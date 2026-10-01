import json
from dataclasses import dataclass
from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.auth import AuthPrincipal, get_current_principal
from app.bank.contracts import BANK_PORTAL_ROLES
from app.bank.developer_service import hash_secret
from app.bank.models import BankApiKey
from app.database import get_db

api_key_header = APIKeyHeader(name="X-Sura-API-Key", auto_error=False)


@dataclass(frozen=True)
class BankApiPrincipal:
    bank_id: str
    api_key_id: str
    scopes: frozenset[str]


def get_bank_principal(current: AuthPrincipal = Depends(get_current_principal)) -> AuthPrincipal:
    if current.role not in BANK_PORTAL_ROLES or not current.institution_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bank Portal access is required.")
    return current


def require_bank_permission(permission: str):
    def dependency(current: AuthPrincipal = Depends(get_bank_principal)) -> AuthPrincipal:
        if current.role != "bank_admin" and permission not in current.permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing required bank permission.")
        return current
    return dependency


def get_bank_api_principal(
    raw_api_key: str | None = Depends(api_key_header),
    db: Session = Depends(get_db),
) -> BankApiPrincipal:
    if not raw_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key authentication is required.")
    key = db.query(BankApiKey).filter(BankApiKey.secret_hash == hash_secret(raw_api_key)).one_or_none()
    if key is None or key.revoked_at is not None or (key.expires_at is not None and key.expires_at <= datetime.utcnow()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid, expired, or revoked API key.")
    key.last_used_at = datetime.utcnow()
    db.commit()
    return BankApiPrincipal(bank_id=key.bank_id, api_key_id=key.id, scopes=frozenset(json.loads(key.scopes_json)))


def require_api_scope(scope: str):
    def dependency(current: BankApiPrincipal = Depends(get_bank_api_principal)) -> BankApiPrincipal:
        if scope not in current.scopes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key does not have the required scope.")
        return current
    return dependency
