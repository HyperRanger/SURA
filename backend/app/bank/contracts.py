"""JWT contract for Bank Portal access.

``institution_id`` is the external identity-provider claim. Its value maps to
the internal ``bank_id`` tenant key stored in Sura's database.
"""
BANK_PORTAL_ROLES = frozenset({"bank_admin", "bank_risk_analyst", "bank_integration_engineer"})
REQUIRED_BANK_CLAIMS = frozenset({"sub", "role", "institution_id", "permissions"})
