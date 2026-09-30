"""JWT and HTTP contracts for Bank Portal access.

``institution_id`` is the external identity-provider claim. Its value maps to
the internal ``bank_id`` tenant key stored in Sura's database.
"""
BANK_PORTAL_ROLES = frozenset({"bank_admin", "bank_risk_analyst", "bank_integration_engineer"})
REQUIRED_BANK_CLAIMS = frozenset({"sub", "role", "institution_id", "permissions"})

BANK_STAFF_ROLE_PERMISSIONS = {
    "bank_admin": frozenset({"bank:overview:read", "bank:users:read", "bank:commitments:read", "bank:flags:read", "bank:flags:write", "bank:audit:read", "bank:settlements:read", "bank:developer:write", "bank:team:write", "bank:settings:write"}),
    "bank_risk_analyst": frozenset({"bank:overview:read", "bank:users:read", "bank:commitments:read", "bank:flags:read", "bank:flags:write", "bank:audit:read", "bank:settlements:read"}),
    "bank_integration_engineer": frozenset({"bank:developer:write"}),
}

WEBHOOK_EVENTS = (
    "contribution.recorded",
    "cycle.paid",
    "voucher.issued",
    "voucher.redeemed",
    "score.updated",
    "flag.created",
)

BANK_API_SCOPES = frozenset({"score:read", "commitments:read"})
