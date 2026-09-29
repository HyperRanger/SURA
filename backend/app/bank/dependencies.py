from fastapi import Depends, HTTPException, status

from app.auth import AuthPrincipal, get_current_principal
from app.bank.contracts import BANK_PORTAL_ROLES


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
