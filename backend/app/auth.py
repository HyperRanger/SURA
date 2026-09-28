from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.security import verify_token

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class AuthPrincipal:
    user_id: str
    role: str | None = None
    permissions: tuple[str, ...] = ()
    can_verify_vendor: bool = False

    @property
    def can_redeem_vendor_vouchers(self) -> bool:
        return self.role == "vendor" or "vendor:redeem" in self.permissions


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthPrincipal:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    try:
        claims = verify_token(credentials.credentials)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token.") from exc

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token.")

    role = claims.get("role")
    permissions = claims.get("permissions") or []
    can_verify_vendor = role in {"admin", "verifier"} or "vendor:verify" in permissions
    return AuthPrincipal(
        user_id=user_id,
        role=role,
        permissions=tuple(permissions),
        can_verify_vendor=can_verify_vendor,
    )
