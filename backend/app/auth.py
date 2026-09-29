from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from core.security import is_local_session, verify_token

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class AuthPrincipal:
    user_id: str
    role: str | None = None
    institution_id: str | None = None
    permissions: frozenset[str] = frozenset()

    @property
    def can_verify_vendor(self) -> bool:
        return self.role in {"admin", "verifier"} or "vendor:verify" in self.permissions

    @property
    def can_redeem_vendor_vouchers(self) -> bool:
        return self.role == "vendor" or "vendor:redeem" in self.permissions


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
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

    if is_local_session(claims):
        # The token is only a statement about who signed in, not about what they
        # may do now. The database decides, so a demoted or deleted account stops
        # working on the next request rather than when the token happens to
        # expire. Claim permissions are dropped for the same reason: nothing here
        # grants them, so accepting them would mean trusting the token on the one
        # question the re-check exists to answer.
        user = db.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is no longer active.")
        return AuthPrincipal(
            user_id=user.id,
            role=user.role,
            institution_id=user.institution_id,
            permissions=frozenset(),
        )

    # Externally issued token, trusted on its claims per the provider contract.
    return AuthPrincipal(
        user_id=user_id,
        role=claims.get("role"),
        institution_id=claims.get("institution_id"),
        permissions=frozenset(claims.get("permissions") or []),
    )
