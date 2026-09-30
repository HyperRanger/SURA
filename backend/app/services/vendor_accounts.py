"""Shared vendor-account lookups.

Vendor vouchers belong to a merchant record, while authentication belongs to a
user account. Keeping that translation here prevents each vendor-facing route
from guessing that a user ID and a vendor ID are the same thing.
"""

from fastapi import HTTPException, status

from app.auth import AuthPrincipal


def get_authenticated_vendor_id(principal: AuthPrincipal) -> str:
    """Return the verified merchant identity bound to a vendor session.

    First-party Sura sessions carry ``users.vendor_id`` after the authentication
    dependency has re-checked the account in the database. The direct vendor-ID
    fallback is reserved for an external merchant-scoped token, whose subject
    is the merchant ID by contract. No database query happens here: this helper
    may run immediately before an atomic redemption transaction.
    """
    if principal.vendor_id:
        return principal.vendor_id
    if not principal.is_local_session:
        return principal.user_id

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Vendor account is not linked to a merchant record.",
    )
